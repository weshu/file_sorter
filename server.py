from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from pathlib import Path

from src.file_scanner import FileScanner
from src.categorizer import Categorizer
from src.history_manager import HistoryManager
from src.file_mover import FileMover


app = Flask(__name__, static_folder="static")
app.config["SECRET_KEY"] = "downloads_organizer_secret"
socketio = SocketIO(app, cors_allowed_origins="*")

_scanner = None
_categorizer = None
_history_manager = None
_file_mover = None


def create_app(scanner, categorizer, history_manager, file_mover):
    global _scanner, _categorizer, _history_manager, _file_mover
    _scanner = scanner
    _categorizer = categorizer
    _history_manager = history_manager
    _file_mover = file_mover
    return app


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/scan")
def api_scan():
    files = _scanner.scan(_scanner.files[0].path.parent)
    return jsonify({
        "total": len(files),
        "files": [
            {
                "name": f.name,
                "size": f.size,
                "extension": f.extension,
                "modified": f.modified.isoformat(),
                "file_type": f.file_type,
                "path": str(f.path),
            }
            for f in files
        ]
    })


@app.route("/api/files")
def api_files():
    current, total = _scanner.get_progress()
    current_file = _scanner.get_current()
    
    current_file_path = str(current_file.path) if current_file else None
    
    existing_files = [f for f in _scanner.files if f.path.exists()]
    
    if current_file_path:
        new_index = None
        for i, f in enumerate(existing_files):
            if str(f.path) == current_file_path:
                new_index = i
                break
        
        if new_index is not None:
            _scanner.current_index = new_index
        else:
            _scanner.next()
            current_file = _scanner.get_current()
    
    _scanner.files = existing_files
    current, total = _scanner.get_progress()
    current_file = _scanner.get_current()
    
    return jsonify({
        "current": current,
        "total": total,
        "current_file": {
            "name": current_file.name,
            "size": current_file.size,
            "extension": current_file.extension,
            "modified": current_file.modified.isoformat(),
            "file_type": current_file.file_type,
            "path": str(current_file.path),
        } if current_file else None,
        "files": [
            {
                "name": f.name,
                "path": str(f.path),
            }
            for f in _scanner.files
        ]
    })


@app.route("/api/files/<int:index>")
def api_file_info(index):
    if 0 <= index < len(_scanner.files):
        f = _scanner.files[index]
        return jsonify({
            "name": f.name,
            "size": f.size,
            "extension": f.extension,
            "modified": f.modified.isoformat(),
            "file_type": f.file_type,
            "path": str(f.path),
        })
    return jsonify({"error": "File not found"}), 404


@app.route("/api/base-path")
def api_base_path():
    return jsonify({"base_path": str(_categorizer.get_base_path())})


@app.route("/api/search-folders", methods=["GET"])
def api_search_folders():
    query = request.args.get("q", "")
    base = _categorizer.get_base_path()
    
    folders = []
    
    if not query:
        if base.exists():
            for item in sorted(base.iterdir()):
                if item.is_dir():
                    rel_path = item.relative_to(base)
                    folders.append(str(rel_path))
    else:
        query_path = Path(query).expanduser()
        
        if query_path.exists() and query_path.is_dir():
            for item in sorted(query_path.iterdir()):
                if item.is_dir():
                    folders.append(str(item))
        else:
            if str(query_path).startswith(str(base)):
                parent_path = query_path.parent
                if parent_path.exists() and parent_path.is_dir():
                    prefix = query_path.name.lower()
                    for item in sorted(parent_path.iterdir()):
                        if item.is_dir() and item.name.lower().startswith(prefix):
                            folders.append(str(item))
            else:
                search_path = query_path.parent
                if search_path.exists():
                    prefix = query_path.name.lower()
                    for item in sorted(search_path.iterdir()):
                        if item.is_dir() and item.name.lower().startswith(prefix):
                            folders.append(str(item))
    
    return jsonify({"folders": folders[:20]})


@app.route("/api/nearby-folders/<path:path>")
def api_nearby_folders(path):
    base = _categorizer.get_base_path()
    full_path = base / path
    
    folders = []
    if full_path.exists() and full_path.is_dir():
        for item in full_path.iterdir():
            if item.is_dir():
                rel_path = item.relative_to(base)
                folders.append(str(rel_path))
    
    return jsonify({"folders": folders})


@app.route("/api/move", methods=["POST"])
def api_move():
    data = request.json
    destination = data.get("destination")
    
    current_file = _scanner.get_current()
    if not current_file:
        return jsonify({"error": "No file to move"}), 400
    
    if not destination:
        return jsonify({"error": "Destination required"}), 400
    
    base_path = _categorizer.get_base_path()
    
    dest_path = Path(destination)
    if dest_path.is_absolute() and str(dest_path).startswith(str(base_path)):
        relative_dest = str(dest_path)[len(str(base_path)):].lstrip('/')
    else:
        relative_dest = destination
    
    full_destination = base_path / relative_dest / current_file.name
    
    try:
        moved_path = _file_mover.move(current_file.path, full_destination)
        
        _history_manager.add_destination(str(base_path / relative_dest))
        
        current, total = _scanner.get_progress()
        _history_manager.save_state(current, total)
        
        emit_update("progress_updated", {})
        
        _scanner.next()
        emit_update("file_updated", {})
        
        return jsonify({
            "success": True,
            "moved_to": str(moved_path),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/skip", methods=["POST"])
def api_skip():
    _scanner.skip()
    emit_update("file_updated", {})
    
    return jsonify({
        "success": True,
        "current": _scanner.get_progress()[0],
        "total": _scanner.get_progress()[1],
    })


@app.route("/api/history")
def api_history():
    recent = _history_manager.get_recent_destinations(20)
    return jsonify({"destinations": recent})


@app.route("/api/history", methods=["POST"])
def api_add_history():
    data = request.json
    destination = data.get("destination")
    
    if destination:
        _history_manager.add_destination(destination)
        emit_update("history_updated", {})
    
    return jsonify({"success": True})


@app.route("/api/rename", methods=["POST"])
def api_rename():
    data = request.json
    new_name = data.get("new_name")
    
    current_file = _scanner.get_current()
    if not current_file:
        return jsonify({"error": "No file to rename"}), 400
    
    if not new_name:
        return jsonify({"error": "New name required"}), 400
    
    new_path = current_file.path.parent / new_name
    
    try:
        current_file.path.rename(new_path)
        current_file.path = new_path
        current_file.name = new_name
        
        return jsonify({"success": True, "new_path": str(new_path)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rollback", methods=["POST"])
def api_rollback():
    try:
        success = _file_mover.rollback()
        if success:
            emit_update("file_updated", {})
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/state")
def api_state():
    current, total = _scanner.get_progress()
    saved = _history_manager.load_state()
    
    return jsonify({
        "current": current,
        "total": total,
        "saved": saved,
    })


def emit_update(event, data):
    socketio.emit(event, data)


@socketio.on("connect")
def handle_connect():
    emit("connected", {"status": "ok"})


@socketio.on("request_update")
def handle_update():
    current, total = _scanner.get_progress()
    current_file = _scanner.get_current()
    
    emit("file_updated", {
        "current": current,
        "total": total,
        "current_file": {
            "name": current_file.name,
            "size": current_file.size,
            "extension": current_file.extension,
            "modified": current_file.modified.isoformat(),
            "file_type": current_file.file_type,
            "path": str(current_file.path),
        } if current_file else None,
    })


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
