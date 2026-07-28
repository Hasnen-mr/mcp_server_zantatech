# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any

_logger = logging.getLogger(__name__)

class CapabilityManager:
    SUPPORTED_PROTOCOL_VERSIONS = ["2024-11-05", "2024-10-07"]

    def __init__(self):
        _logger.debug("Initializing CapabilityManager")

    def negotiate_capabilities(self, client_capabilities: Dict[str, Any], active_profile: str) -> Dict[str, Any]:
        return {
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False},
            "prompts": {"listChanged": False}
        }
