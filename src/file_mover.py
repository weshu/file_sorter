from pathlib import Path
import shutil
from typing import Optional, Tuple


class FileMover:
    def __init__(self):
        self.last_move = None

    def move(self, source, destination):
        source = Path(source).expanduser()
        destination = Path(destination).expanduser()
        
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        final_destination = self.get_unique_name(destination)
        
        shutil.move(str(source), str(final_destination))
        
        self.last_move = (source, final_destination)
        
        return final_destination

    def get_unique_name(self, destination):
        destination = Path(destination)
        
        if not destination.exists():
            return destination
        
        stem = destination.stem
        suffix = destination.suffix
        parent = destination.parent
        counter = 1
        
        while True:
            new_name = "{} ({}){}".format(stem, counter, suffix)
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def handle_conflict(self, source, destination):
        return self.get_unique_name(destination)

    def rollback(self):
        if not self.last_move:
            return False
        
        source, destination = self.last_move
        
        if destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(source))
            self.last_move = None
            return True
        
        return False
