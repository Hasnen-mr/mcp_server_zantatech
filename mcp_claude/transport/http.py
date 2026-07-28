# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any

_logger = logging.getLogger(__name__)

class HTTPTransportHandler:
    def __init__(self):
        _logger.debug("Initializing HTTPTransportHandler")

    def parse_request(self, raw_payload: bytes) -> Dict[str, Any]:
        return {}

    def format_response(self, result: Dict[str, Any]) -> str:
        return "{}"
