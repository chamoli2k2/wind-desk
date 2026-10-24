"""Immutable JSON snapshot repository. No database needed for a fixed-month pilot."""
import json
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=4)
def _read(path, modified):
    return json.loads(Path(path).read_text())


class Repository:
    def __init__(self, directory):
        self.path = Path(directory) / 'snapshot.json'

    def load(self):
        return _read(str(self.path), self.path.stat().st_mtime_ns)
