import logging
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

class ModelPermissionEvaluator:
    def check_permission(self, client_id: int, user_id: int, model_name: str, operation: str) -> bool:
        op = (operation or '').lower()
        if op not in ['read', 'search', 'select', 'get', 'explain', 'aggregate']:
            _logger.warning(f"Mutation operation '{operation}' rejected on model '{model_name}'. Read-only mode enforced.")
            raise AccessError("This MCP deployment is currently configured for read-only access.")
        return True
