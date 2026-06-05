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
    parts = [secure_filename(part) for part in normalized.split("/") if part and part not in (".", "..")] 
    return "/".join(parts)

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
                game_name = os.path.splitext(rel_path)[0]
                game_name = game_name.replace(" [original]", "")
                game_name = re.sub(r"(\]\s)(\[\d+\])$", r"]\2", game_name)
                if filter_by_name:
                    search_term_lower = request_char.lower()
                    game_name_lower = game_name.lower()
                    if search_term_lower != "a":
                        if len(search_term_lower) == 1:
                            if not game_name_lower.startswith(search_term_lower):
                                continue
                        else:
                            if search_term_lower not in game_name_lower:
                                continue
                entries.append((game_name, size, rel_path))
    unique = []
    seen = set()
    for entry in sorted(entries, key=lambda item: (item[0], item[2])):
        if entry not in seen:
            unique.append(entry)
            seen.add(entry)
    return unique

def list_directory_structured():
    """Returns a list of dictionaries representing the file structure."""
    items = []
    for root, dirs, files in os.walk(SERVE_DIRECTORY):
        rel_root = os.path.relpath(root, SERVE_DIRECTORY)
        # Normalize rel_root to forward slashes
        display_root = "/" if rel_root == "." else "/" + rel_root.replace(os.sep, "/")
        
        # Add directories (except root)
        if rel_root != ".":
            items.append({
                "name": os.path.basename(root),
                "path": rel_root.replace(os.sep, "/"),
                "type": "dir",
                "display_path": display_root
            })
            
        for filename in sorted(files):
            file_rel_path = os.path.join(rel_root, filename)
            if rel_root == ".":
                file_rel_path = filename
                
            items.append({
                "name": filename,
                "path": file_rel_path.replace(os.sep, "/"),
                "type": "file",
                "display_path": display_root
            })
    
    # Sort by path so it looks like a tree
    return sorted(items, key=lambda x: x["path"])
