# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import Response

_logger = logging.getLogger(__name__)

class MCPOAuthController(http.Controller):
    @http.route('/mcp/oauth/authorize', type='http', auth='user', methods=['GET', 'POST'], csrf=True)
    def authorize(self, **kwargs):
        _logger.info("OAuth authorize endpoint hit")
        return Response('{"status": "Not Implemented"}', status=501, content_type='application/json')

    @http.route('/mcp/oauth/token', type='http', auth='none', methods=['POST'], csrf=False)
    def token(self, **kwargs):
        _logger.info("OAuth token endpoint hit")
        return Response('{"status": "Not Implemented"}', status=501, content_type='application/json')

    @http.route('/mcp/oauth/revoke', type='http', auth='none', methods=['POST'], csrf=False)
    def revoke(self, **kwargs):
        _logger.info("OAuth revoke endpoint hit")
        return Response('{"status": "Not Implemented"}', status=501, content_type='application/json')
