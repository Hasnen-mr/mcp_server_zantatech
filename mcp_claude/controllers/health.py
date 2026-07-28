# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import Response

_logger = logging.getLogger(__name__)

class MCPHealthController(http.Controller):
    @http.route('/mcp/health', type='http', auth='none', methods=['GET'], csrf=False)
    def health_check(self, **kwargs):
        _logger.info("MCP Health check requested")
        return Response(
            '{"status": "healthy", "version": "1.0.0", "message": "Placeholder - Not Implemented"}',
            status=200,
            content_type='application/json'
        )
