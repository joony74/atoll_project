"""Named entry points for CocoAi Study architecture layers.

These modules are intentionally thin at first. The goal is to make the
architecture explicit in code so future changes land in the correct layer
instead of growing `app.py` further.
"""

from .persistence import JsonFileRepository, StorageRepository

__all__ = ["JsonFileRepository", "StorageRepository"]
