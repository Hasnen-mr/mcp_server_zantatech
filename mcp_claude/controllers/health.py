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

    @http.route([
        '/.well-known/oauth-protected-resource',
        '/.well-known/oauth-protected-resource/mcp/v1/sse',
        '/.well-known/oauth-protected-resource/mcp'
    ], type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def oauth_protected_resource_metadata(self, **kwargs):
        _logger.info("RFC 9728 OAuth Protected Resource Metadata requested")
        headers = [
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
        ]
        if http.request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=headers)
        
        scheme = http.request.httprequest.headers.get('X-Forwarded-Proto', 'https')
        host = http.request.httprequest.host
        base_url = f"{scheme}://{host}".rstrip('/')
        payload = {
            "resource": f"{base_url}/mcp",
            "authorization_servers": [
                base_url
            ],
            "scopes_supported": [
                "mcp:read",
                "mcp:write"
            ]
        }
        import json
        return Response(
            json.dumps(payload, indent=2),
            status=200,
            headers=headers
        )
