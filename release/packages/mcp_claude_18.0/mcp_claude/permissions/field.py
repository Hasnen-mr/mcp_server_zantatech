# -*- coding: utf-8 -*-
import logging
from typing import List, Dict, Any

_logger = logging.getLogger(__name__)

class FieldPermissionEvaluator:
    def filter_fields(self, model_name: str, record_dict: Dict[str, Any], allowed_fields: List[str], excluded_fields: List[str]) -> Dict[str, Any]:
        return record_dict
