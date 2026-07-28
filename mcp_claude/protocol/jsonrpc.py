# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any

_logger = logging.getLogger(__name__)

class JSONRPCParser:
    def parse_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return payload

    def build_result(self, request_id: Any, result_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result_data}
