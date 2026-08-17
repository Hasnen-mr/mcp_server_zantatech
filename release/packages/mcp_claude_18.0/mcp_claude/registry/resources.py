# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any, List

_logger = logging.getLogger(__name__)

class ResourceRegistry:
    def list_resources(self) -> List[Dict[str, Any]]:
        return []
