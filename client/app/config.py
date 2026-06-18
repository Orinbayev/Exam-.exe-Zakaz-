"""
Client konfiguratsiyasi - server manzili va sozlamalar.
"""
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")

DEFAULT_CONFIG = {
    "server_url": "https://exam-exe-zakaz-production.up.railway.app",
    "timeout": 15,
}


class Config:
    _data: dict = {}

    @classmethod
    def load(cls):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    cls._data = {**DEFAULT_CONFIG, **json.load(f)}
                return
            except Exception:
                pass
        cls._data = DEFAULT_CONFIG.copy()

    @classmethod
    def save(cls):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(cls._data, f, indent=2)
        except Exception:
            pass

    @classmethod
    def get(cls, key: str, default=None):
        if not cls._data:
            cls.load()
        return cls._data.get(key, default)

    @classmethod
    def set(cls, key: str, value):
        if not cls._data:
            cls.load()
        cls._data[key] = value
        cls.save()

    @classmethod
    def server_url(cls) -> str:
        url = cls.get("server_url", "http://127.0.0.1:8000")
        return url.rstrip("/")


Config.load()
