# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any

_logger = logging.getLogger(__name__)

class SchemaGenerator:
    def generate_model_schema(self, model_name: str, allowed_fields: list = None) -> Dict[str, Any]:
        return {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object", "properties": {}}
