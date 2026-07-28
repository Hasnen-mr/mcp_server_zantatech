# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any

_logger = logging.getLogger(__name__)

class ProfileService:
    def __init__(self, env):
        self.env = env

    def get_active_profile_settings(self) -> Dict[str, Any]:
        return {"profile": "development", "debug_logging": True, "strict_rate_limit": False}
