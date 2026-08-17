# -*- coding: utf-8 -*-
import logging
from typing import Optional, Any

_logger = logging.getLogger(__name__)

class PermissionCache:
    _cache = {}

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        return cls._cache.get(key)

    @classmethod
    def set(cls, key: str, value: Any):
        cls._cache[key] = value

    @classmethod
    def invalidate_all(cls):
        cls._cache.clear()
