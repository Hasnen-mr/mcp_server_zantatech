# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

class ModelPermissionEvaluator:
    def check_permission(self, client_id: int, user_id: int, model_name: str, operation: str) -> bool:
        return True
