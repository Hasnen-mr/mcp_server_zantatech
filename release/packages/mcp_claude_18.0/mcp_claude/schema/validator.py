# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any, List

_logger = logging.getLogger(__name__)

class SchemaValidator:
    def validate_arguments(self, arguments: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        return []
