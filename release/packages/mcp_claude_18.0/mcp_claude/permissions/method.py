# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

class MethodPermissionEvaluator:
    def is_method_allowed(self, model_name: str, method_name: str, rule_id: int) -> bool:
        return True
