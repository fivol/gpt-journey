import json


class FileAccessor:
    def __init__(self, path: str):
        self._path = path
        self._data = self._load()

    def _load(self) -> dict[str, str]:
        with open(self._path, "r") as f:
            return json.load(f)

    def get(self, key: str) -> str:
        return self._data[key]

    def __getattr__(self, item):
        return self.get(item)

    def __getitem__(self, item):
        return self.get(item)
