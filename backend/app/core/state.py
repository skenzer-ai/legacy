from enum import Enum
import json
import os
from threading import Lock
from app.core.config import settings

class ProcessingStatus(str, Enum):
    UNPROCESSED = "UNPROCESSED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    ERROR = "ERROR"

class ProcessingStateManager:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.states = {}
                cls._instance._load_state_from_disk()
        return cls._instance

    def _load_state_from_disk(self):
        if os.path.exists(settings.STATE_FILE):
            with open(settings.STATE_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    self.states = {k: ProcessingStatus(v) for k, v in data.items()}
                except (json.JSONDecodeError, TypeError):
                    self._initialize_default_state()
        else:
            self._initialize_default_state()
        print(f"Initial state loaded: {self.states}")

    def _save_state_to_disk(self):
        with open(settings.STATE_FILE, 'w') as f:
            # Convert Enum members to their string values for JSON serialization
            data_to_save = {k: v.value for k, v in self.states.items()}
            json.dump(data_to_save, f, indent=4)

    def _initialize_default_state(self):
        self.states = {
            "document": ProcessingStatus.UNPROCESSED,
            "api": ProcessingStatus.UNPROCESSED,
        }
        self._save_state_to_disk()

    def get_status(self, source: str) -> ProcessingStatus:
        return self.states.get(source, ProcessingStatus.UNPROCESSED)

    def set_status(self, source: str, status: ProcessingStatus):
        if source in self.states:
            print(f"Updating status for '{source}' to '{status.value}'")
            self.states[source] = status
            self._save_state_to_disk()

# Singleton instance
state_manager = ProcessingStateManager()