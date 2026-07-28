# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any

_logger = logging.getLogger(__name__)

class MCPServer:
    def __init__(self):
        _logger.debug("Initializing MCPServer instance")

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "Odoo MCP Claude", "version": "18.0.1.0.0"}
        }
