# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any

_logger = logging.getLogger(__name__)

class ApprovalService:
    def __init__(self, env):
        self.env = env

    def create_approval_request(self, tool_name: str, client_id: int, user_id: int, payload: Dict[str, Any]) -> int:
        return 0
