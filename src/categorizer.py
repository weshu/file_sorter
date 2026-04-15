from pathlib import Path
from typing import List


class Categorizer:
    def __init__(self, base_path):
        self.base_path = Path(base_path).expanduser()

    def get_base_path(self):
        return self.base_path

    def get_all_folders(self):
        if not self.base_path.exists():
            return []
        
        folders = []
        for item in self.base_path.rglob("*"):
            if item.is_dir():
                rel_path = item.relative_to(self.base_path)
                if str(rel_path) != ".":
                    folders.append(str(rel_path))
        
        return sorted(folders)
