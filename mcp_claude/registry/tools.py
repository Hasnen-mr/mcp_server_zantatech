# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any, List, Callable

_logger = logging.getLogger(__name__)
_REGISTERED_TOOLS: Dict[str, Dict[str, Any]] = {}

def mcp_tool(name: str, version: str = "1.0.0", category: str = "General",
             description: str = "", risk_level: str = "Low",
             read_only: bool = False, requires_approval: bool = False, author: str = "Core"):
    def decorator(func: Callable):
        tool_meta = {
            "name": name,
            "version": version,
            "category": category,
            "description": description or func.__doc__ or "",
            "risk_level": risk_level,
            "read_only": read_only,
            "requires_approval": requires_approval,
            "author": author,
            "handler": func
        }
        _REGISTERED_TOOLS[name] = tool_meta
        return func
    return decorator

class ToolRegistry:
    @classmethod
    def get_all_tools(cls) -> List[Dict[str, Any]]:
        return list(_REGISTERED_TOOLS.values())

    @classmethod
    def get_tool(cls, name: str) -> Dict[str, Any]:
        return _REGISTERED_TOOLS.get(name)
