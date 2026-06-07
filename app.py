#!/usr/bin/env python3
"""
Flask webserver that returns plain text directory listing from files/ directory
"""

import os
import sys
import shutil
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, Response, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename

from utils import (
    SERVE_DIRECTORY,
    safe_path,
    list_file_entries,
    list_directory_structured,
)
from translations import TRANSLATIONS

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Logging Configuration ---

if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s'
))
stream_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)
app.logger.addHandler(stream_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('msx-flask startup')

# --- DRY Helpers ---

def get_msg(key):
    """Get translated message based on current session language."""
    lang = session.get('lang', 'nl')
    return TRANSLATIONS.get(lang, {}).get(key, key)

def render_manage(message=None):
    """Helper to consistently render the manage page with listing."""
    return render_template("manage.html", message=message, items=list_directory_structured())

# --- Context Processors ---

@app.context_processor
def inject_translate():
    lang = session.get('lang', 'nl')
    return dict(_=lambda key: TRANSLATIONS.get(lang, {}).get(key, key), current_lang=lang)

# --- Logging Hooks ---

@app.before_request
def log_request():
    """Log every single request, even if it doesn't match a route."""
    app.logger.info(f"Incoming: {request.method} {request.url} from {request.remote_addr} (UA: {request.user_agent})")
    app.logger.debug(f"Headers: {dict(request.headers)}")

# --- Routes ---

@app.route("/set_lang/<lang>")
def set_lang(lang):
    if lang in TRANSLATIONS:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/manage")
def manage():
    return render_manage()

@app.route("/manage/upload", methods=["POST"])
def upload_file():
    upload = request.files.get("file")
    if not upload or upload.filename == "":
        return render_manage(get_msg("msg_select_file"))
    
    filename = secure_filename(upload.filename)
    if not filename:
        return render_manage(get_msg("msg_invalid_filename"))
    
    target_dir = request.form.get("target_dir", "")
    try:
        dest_dir = safe_path(target_dir)
    except ValueError:
        return render_manage(get_msg("msg_invalid_path"))
    
    os.makedirs(dest_dir, exist_ok=True)
    destination = os.path.join(dest_dir, filename)
    destination = safe_path(os.path.relpath(destination, SERVE_DIRECTORY))
    upload.save(destination)
    
    rel_path = os.path.relpath(destination, SERVE_DIRECTORY).replace('\\', '/')
    app.logger.info(f"File uploaded: {rel_path} from {request.remote_addr}")
    return render_manage(f"{get_msg('msg_upload_success')} /{rel_path}.")

@app.route("/manage/delete", methods=["POST"])
def delete_item():
    target = request.form.get("path", "")
    if not target:
        return render_manage(get_msg("msg_provide_path"))
    
    try:
        target_path = safe_path(target)
    except ValueError:
        return render_manage(get_msg("msg_invalid_path"))
    
    if not os.path.exists(target_path):
        return render_manage(get_msg("msg_not_found"))
    
    if os.path.abspath(target_path) == os.path.abspath(SERVE_DIRECTORY):
        return render_manage(get_msg("msg_root_delete_denied"))
    
    if os.path.isdir(target_path):
        shutil.rmtree(target_path)
    else:
        os.remove(target_path)
    
    rel_path = os.path.relpath(target_path, SERVE_DIRECTORY).replace('\\', '/')
    app.logger.info(f"Item deleted: {rel_path} by {request.remote_addr}")
    return render_manage(f"{get_msg('msg_deleted')} /{rel_path}.")

@app.route("/manage/rename", methods=["POST"])
def rename_item():
    old_path = request.form.get("old_path", "")
    new_path = request.form.get("new_path", "")
    if not old_path or not new_path:
        return render_manage(get_msg("msg_provide_both_paths"))
    
    try:
        source_path = safe_path(old_path)
        destination_path = safe_path(new_path)
    except ValueError:
        return render_manage(get_msg("msg_invalid_path"))
    
    if not os.path.exists(source_path):
        return render_manage(get_msg("msg_source_not_found"))
    
    if os.path.exists(destination_path):
        return render_manage(get_msg("msg_dest_exists"))
    
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    os.rename(source_path, destination_path)
    
    rel_old = os.path.relpath(source_path, SERVE_DIRECTORY).replace('\\', '/')
    rel_new = os.path.relpath(destination_path, SERVE_DIRECTORY).replace('\\', '/')
    app.logger.info(f"Item renamed: {rel_old} to {rel_new} by {request.remote_addr}")
    return render_manage(f"{get_msg('msg_moved')} /{rel_old} {get_msg('msg_to')} /{rel_new}.")

@app.route("/manage/mkdir", methods=["POST"])
def make_dir():
    dir_path = request.form.get("dir_path", "")
    if not dir_path:
        return render_manage(get_msg("msg_provide_dirname"))
    
    try:
        destination = safe_path(dir_path)
    except ValueError:
        return render_manage(get_msg("msg_invalid_path"))
    
    if os.path.isfile(destination):
        return render_manage(get_msg("msg_file_exists"))
    
    os.makedirs(destination, exist_ok=True)
    rel_path = os.path.relpath(destination, SERVE_DIRECTORY).replace('\\', '/')
    app.logger.info(f"Directory created: {rel_path} by {request.remote_addr}")
    return render_manage(f"{get_msg('msg_mkdir_success')} /{rel_path}.")

@app.route("/index2.php")
@app.route("/index2.php/")
def directory_listing():
    """Return directory listing based on type parameter (ROM or DSK)"""
    app.logger.info(f"API Request: {request.url} from {request.remote_addr} (UA: {request.user_agent})")
    request_type = request.args.get("type", "ROM").upper()
    request_char = request.args.get("char", "a")
    download_index = request.args.get("download", None)

    if request_type == "ROM":
        extensions = [".rom", ".ROM"]
    elif request_type == "DSK":
        extensions = [".dsk", ".DSK"]
    else:
        app.logger.warning(f"Unsupported type: {request_type}")
        return f"Error: Unsupported type '{request_type}'. Use ROM or DSK.", 400

    files = list_file_entries(extensions, request_char=request_char)

    if download_index is not None:
        if not download_index.isdigit():
            return f"Error: Invalid download index {download_index}.", 400
        download_idx = int(download_index)
        if not 0 <= download_idx < len(files):
            return f"Error: Invalid download index {download_idx}.", 400

        game_name, size, rel_path = files[download_idx]
        item_path = safe_path(rel_path)
        app.logger.info(f"Downloading file: {rel_path} for {request.remote_addr}")
        try:
            with open(item_path, "rb") as f:
                file_content = f.read()
            
            header = f"{'size:' if request_type == 'DSK' else 'type:,start:,size:'}{len(file_content)}{',disks:1' if request_type == 'DSK' else ''},name:{game_name}.{request_type.lower()}"

            def generate():
                yield header.encode("utf-8")
                yield b"\n"
                yield file_content

            response = Response(generate())
            response.headers["Content-type"] = "text/html; charset=UTF-8"
            response.headers["Expires"] = "0"
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Server"] = "Abyss/2.16.20.2-X2-Win32 AbyssLib/2.16.20.2"
            response.headers["X-Powered-By"] = "PHP/8.5.5"
            return response
        except (OSError, IOError) as e:
            app.logger.error(f"Error reading file {item_path}: {e}")
            return f"Error reading file: {str(e)}", 500

    result = "".join(f"{game_name}\t{size}\n" for game_name, size, _ in files) if files else "No files found\t0\n"

    def generate_listing():
        yield result.encode("utf-8")

    response = Response(generate_listing())
    response.headers["Content-type"] = "text/html; charset=UTF-8"
    response.headers["Expires"] = "0"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Server"] = "Abyss/2.16.20.2-X2-Win32 AbyssLib/2.16.20.2"
    response.headers["X-Powered-By"] = "PHP/8.5.5"
    return response

@app.route("/<path:path>")
def catch_all(path):
    app.logger.warning(f"404 Path not found: /{path} from {request.remote_addr} (Args: {dict(request.args)})")
    return f"404 - Path not found: /{path}\nOnly /index2.php/ is supported", 404

if __name__ == "__main__":
    os.makedirs(SERVE_DIRECTORY, exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5001)
