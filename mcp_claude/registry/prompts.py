# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any, List

_logger = logging.getLogger(__name__)

class PromptRegistry:
    def list_prompts(self) -> List[Dict[str, Any]]:
        return []
