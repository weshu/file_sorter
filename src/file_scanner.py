from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json


@dataclass
class FileInfo:
    path: Path
    name: str
    extension: str
    size: int
    modified: datetime
    file_type: str


class FileScanner:
    def __init__(self):
        self.files = []
        self.current_index = 0

    def scan(self, path):
        self.files = []
        path = Path(path).expanduser()
        
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        
        for item in sorted(path.iterdir()):
            if item.is_file() and not item.name.startswith("."):
                file_info = self.get_file_info(item)
                self.files.append(file_info)
        
        return self.files

    def get_file_info(self, filepath: Path) -> FileInfo:
        stat = filepath.stat()
        return FileInfo(
            path=filepath,
            name=filepath.name,
            extension=filepath.suffix.lstrip(".") if filepath.suffix else "",
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime),
            file_type=self._get_file_type(filepath),
        )

    def _get_file_type(self, filepath: Path) -> str:
        suffix = filepath.suffix.lower()
        type_map = {
            ".pdf": "PDF Document",
            ".doc": "Word Document",
            ".docx": "Word Document",
            ".txt": "Text File",
            ".jpg": "JPEG Image",
            ".jpeg": "JPEG Image",
            ".png": "PNG Image",
            ".gif": "GIF Image",
            ".mp4": "Video",
            ".mov": "Video",
            ".mp3": "Audio",
            ".wav": "Audio",
            ".zip": "Archive",
            ".tar": "Archive",
            ".gz": "Archive",
        }
        return type_map.get(suffix, "File")

    def filter_files(self, extensions):
        return [f for f in self.files if f.extension in extensions]

    def get_total_size(self):
        return sum(f.size for f in self.files)

    def save_state(self, state_path):
        state = {
            "current_index": self.current_index,
            "files": [str(f.path) for f in self.files],
        }
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(state, f)

    def load_state(self, state_path):
        if not state_path.exists():
            return False
        
        with open(state_path, "r") as f:
            state = json.load(f)
        
        self.current_index = state.get("current_index", 0)
        
        existing_files = []
        for path_str in state.get("files", []):
            p = Path(path_str)
            if p.exists():
                existing_files.append(self.get_file_info(p))
        
        self.files = existing_files
        return True

    def get_current(self):
        if 0 <= self.current_index < len(self.files):
            return self.files[self.current_index]
        return None

    def next(self):
        if self.current_index < len(self.files) - 1:
            self.current_index += 1
            return self.get_current()
        return None

    def skip(self):
        return self.next()

    def get_progress(self):
        return self.current_index + 1, len(self.files)
