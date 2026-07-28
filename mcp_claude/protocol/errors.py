# -*- coding: utf-8 -*-
from typing import Dict, Any

class MCPErrorCatalog:
    AUTH_FAILED = {"code": "MCP1001", "jsonrpc_code": -32001, "message": "Authentication Failed"}
    PERMISSION_DENIED = {"code": "MCP1002", "jsonrpc_code": -32002, "message": "Permission Denied"}
    TOOL_NOT_FOUND = {"code": "MCP1003", "jsonrpc_code": -32601, "message": "Tool Not Found"}
    INVALID_SCHEMA = {"code": "MCP1004", "jsonrpc_code": -32602, "message": "Invalid Arguments Schema"}
    APPROVAL_REQUIRED = {"code": "MCP1005", "jsonrpc_code": -32005, "message": "Human Approval Required"}
    RATE_LIMIT_EXCEEDED = {"code": "MCP1006", "jsonrpc_code": -32006, "message": "Rate Limit Exceeded"}
    ASYNC_JOB_ENQUEUED = {"code": "MCP1007", "jsonrpc_code": -32007, "message": "Async Background Job Enqueued"}
    PROTOCOL_MISMATCH = {"code": "MCP1008", "jsonrpc_code": -32008, "message": "Protocol Version Incompatible"}
    INTERNAL_ERROR = {"code": "MCP1500", "jsonrpc_code": -32603, "message": "Internal Server Error"}

    @classmethod
    def get_error_response(cls, error_dict: Dict[str, Any], details: str = None) -> Dict[str, Any]:
        return {
            "code": error_dict["jsonrpc_code"],
            "message": error_dict["message"],
            "data": {"mcp_code": error_dict["code"], "details": details or ""}
        }
