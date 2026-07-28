# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any

_logger = logging.getLogger(__name__)

class AuditLoggerService:
    def __init__(self, env):
        self.env = env

    def log_execution(self, log_data: Dict[str, Any]):
        pass
