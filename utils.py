import os
import re
import shutil
import html
from werkzeug.utils import secure_filename

# Configure the directory to serve
BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
SERVE_DIRECTORY = os.path.join(BASE_DIRECTORY, "files")

def safe_relative_path(user_path):
    if user_path is None:
        return ""
    normalized = user_path.strip().replace("\\", "/")
    if normalized in ("", "."):
        return ""
    normalized = os.path.normpath(normalized)
    if normalized.startswith("..") or normalized.startswith("/"):
        raise ValueError("Invalid path")
    return normalized

def safe_path(relative_path):
    relative_path = safe_relative_path(relative_path)
    destination = os.path.normpath(os.path.join(SERVE_DIRECTORY, relative_path))
    if os.path.commonpath([os.path.abspath(SERVE_DIRECTORY), os.path.abspath(destination)]) != os.path.abspath(SERVE_DIRECTORY):
        raise ValueError("Path outside serve directory")
    return destination

def list_file_entries(extensions, request_char="a", filter_by_name=True):
    entries = []
    for root, _, filenames in os.walk(SERVE_DIRECTORY):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, filename)
                if not os.path.isfile(file_path):
                    continue
                rel_path = os.path.relpath(file_path, SERVE_DIRECTORY).replace(os.sep, "/")
                try:
                    size = os.path.getsize(file_path)
                except (OSError, IOError):
                    continue
                
                # Use only the filename without extension for the display name
                display_name = os.path.splitext(filename)[0]
                display_name = display_name.replace(" [original]", "")
                display_name = re.sub(r"(\]\s)(\[\d+\])$", r"]\2", display_name)
                
                if filter_by_name:
                    search_term_lower = request_char.lower()
                    display_name_lower = display_name.lower()
                    if search_term_lower != "a":
                        if len(search_term_lower) == 1:
                            if not display_name_lower.startswith(search_term_lower):
                                continue
                        else:
                            if search_term_lower not in display_name_lower:
                                continue
                entries.append((display_name, size, rel_path))
    unique = []
    seen = set()
    for entry in sorted(entries, key=lambda item: (item[0], item[2])):
        if entry not in seen:
            unique.append(entry)
            seen.add(entry)
    return unique

def list_directory_structured():
    """Returns a list of dictionaries representing the file structure, sorted by path."""
    items = []
    # Add root files first
    for entry in os.scandir(SERVE_DIRECTORY):
        if entry.is_file():
            items.append({
                "name": entry.name,
                "path": entry.name,
                "type": "file",
                "display_path": "/"
            })

    # Now walk subdirectories
    for root, dirs, files in os.walk(SERVE_DIRECTORY):
        rel_root = os.path.relpath(root, SERVE_DIRECTORY)
        if rel_root == ".":
            continue

        clean_rel_root = rel_root.replace(os.sep, "/")
        display_path = "/" + clean_rel_root

        # Add the directory itself
        items.append({
            "name": os.path.basename(root),
            "path": clean_rel_root,
            "type": "dir",
            "display_path": os.path.dirname(display_path)
        })

        # Add files in this directory
        for filename in sorted(files):
            items.append({
                "name": filename,
                "path": clean_rel_root + "/" + filename,
                "type": "file",
                "display_path": display_path
            })

    # Sort by display_path to group them, then by type (dirs first), then name
    return sorted(items, key=lambda x: (x["display_path"], x["type"] == "file", x["name"]))
