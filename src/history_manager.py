import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List


class HistoryManager:
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = Path.home() / ".downloads_organizer"
        
        self.config_dir = Path(config_dir).expanduser()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.destinations_file = self.config_dir / "recent_destinations.json"
        self.preferences_file = self.config_dir / "preferences.json"
        self.state_file = self.config_dir / "state.json"

    def add_destination(self, path):
        destinations = self._load_destinations()
        
        destinations = [d for d in destinations if d["path"] != path]
        
        destinations.insert(0, {
            "path": path,
            "count": 1,
            "last_used": datetime.now().isoformat(),
        })
        
        destinations = destinations[:20]
        
        self._save_destinations(destinations)

    def _load_destinations(self):
        if not self.destinations_file.exists():
            return []
        
        with open(self.destinations_file, "r") as f:
            data = json.load(f)
            return data.get("destinations", [])

    def _save_destinations(self, destinations):
        with open(self.destinations_file, "w") as f:
            json.dump({"destinations": destinations}, f, indent=2)

    def get_recent_destinations(self, n=20):
        destinations = self._load_destinations()
        return [d["path"] for d in destinations[:n]]

    def save_preference(self, key, value):
        prefs = self._load_preferences()
        prefs[key] = value
        self._save_preferences(prefs)

    def _load_preferences(self):
        if not self.preferences_file.exists():
            return {}
        
        with open(self.preferences_file, "r") as f:
            return json.load(f)

    def _save_preferences(self, prefs):
        with open(self.preferences_file, "w") as f:
            json.dump(prefs, f, indent=2)

    def get_preference(self, key, default=None):
        prefs = self._load_preferences()
        return prefs.get(key, default)

    def save_state(self, queue_position, total):
        state = {
            "queue_position": queue_position,
            "total": total,
            "saved_at": datetime.now().isoformat(),
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        if not self.state_file.exists():
            return None
        
        with open(self.state_file, "r") as f:
            return json.load(f)
