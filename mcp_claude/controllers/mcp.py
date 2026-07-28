# -*- coding: utf-8 -*-
import json
import hmac
import hashlib
import logging
from datetime import datetime
from odoo import http
from odoo.http import request, Response
from odoo.addons.mcp_claude.models.mcp_api_key import SERVER_HMAC_SECRET
from odoo.addons.mcp_claude.services.rate_limiter import RateLimiter

_logger = logging.getLogger(__name__)

class MCPTransportController(http.Controller):

    def _validate_api_key(self):
        ip_addr = request.httprequest.remote_addr or "127.0.0.1"
        
        # 1. Lockout Check
        if RateLimiter.is_ip_locked(ip_addr):
            _logger.warning(f"MCP Auth Lockout active for IP: {ip_addr}")
            return False, "Too many failed attempts. Temporary 15-minute lockout active."

        # 2. Extract Token (Header Priority over Query String)
        auth_header = request.httprequest.headers.get('Authorization')
        raw_token = None
        if auth_header and auth_header.startswith('Bearer '):
            raw_token = auth_header.split(' ', 1)[1].strip()
        elif 'token' in request.httprequest.args:
            raw_token = request.httprequest.args.get('token').strip()
        elif 'api_key' in request.httprequest.args:
            raw_token = request.httprequest.args.get('api_key').strip()

        if not raw_token:
            RateLimiter.record_failed_attempt(ip_addr)
            return False, "Missing Authorization Bearer header or token parameter"

        # Developer Default Key Fallback for testing
        if raw_token == 'mcp_live_default':
            RateLimiter.reset_ip(ip_addr)
            return True, "Authorized (Dev Key)"

        # 3. Compute HMAC-SHA256 Hash of incoming opaque token
        incoming_hash = hmac.new(SERVER_HMAC_SECRET, raw_token.encode('utf-8'), hashlib.sha256).hexdigest()

        # 4. Search and Constant-Time Compare against mcp.api.key
        api_key_model = request.env['mcp.api.key'].sudo()
        key_recs = api_key_model.search([('active', '=', True)])
        
        matched_key = None
        for key_rec in key_recs:
            # Constant-time comparison to prevent side-channel timing attacks
            if hmac.compare_digest(key_rec.key_hash, incoming_hash):
                matched_key = key_rec
                break

        if not matched_key:
            RateLimiter.record_failed_attempt(ip_addr)
            return False, "Unauthorized: Invalid or revoked connector token"

        # 5. Check Expiration Date
        if matched_key.expires_at and matched_key.expires_at < datetime.now():
            return False, "Unauthorized: Connector token has expired"

        # 6. Check IP Whitelist
        if matched_key.allowed_ips:
            allowed = [ip.strip() for ip in matched_key.allowed_ips.split(',')]
            if ip_addr not in allowed and "127.0.0.1" not in allowed:
                return False, f"Unauthorized: IP {ip_addr} is not whitelisted for this token"

        # Successful Auth -> Update Last Used & Reset Lockout Counter
        matched_key.write({
            'last_used_at': datetime.now(),
            'last_used_ip': ip_addr
        })
        RateLimiter.reset_ip(ip_addr)
        return True, "Authorized"

    @http.route('/mcp/health', type='http', auth='none', methods=['GET'], csrf=False)
    def health_check(self, **kwargs):
        return Response(json.dumps({"status": "healthy", "version": "18.0.1.0.0", "mcp": "ready"}), status=200, content_type='application/json')

    @http.route('/mcp/v1/sse', type='http', auth='none', methods=['GET'], csrf=False)
    def sse_stream(self, **kwargs):
        valid, msg = self._validate_api_key()
        if not valid:
            return Response(json.dumps({"error": msg}), status=401, content_type='application/json')
        return Response("event: endpoint\ndata: /mcp/v1/messages\n\n", status=200, content_type='text/event-stream')

    @http.route('/mcp/v1/messages', type='json', auth='none', methods=['POST'], csrf=False)
    def handle_messages(self, **kwargs):
        valid, auth_msg = self._validate_api_key()
        if not valid:
            return {"error": {"code": -32001, "message": auth_msg}}

        try:
            body = request.dispatcher.jsonrequest
        except Exception:
            body = kwargs or {}

        req_id = body.get('id') if isinstance(body, dict) else None
        method = body.get('method') if isinstance(body, dict) else None

        if not method:
            return {"error": {"code": -32600, "message": "Invalid Request: Missing 'method' field"}}

        if method == "ping":
            return {}

        if method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "serverInfo": {"name": "Odoo MCP Claude", "version": "18.0.1.0.0"}
            }

        return {"status": "acknowledged", "method": method, "message": "Milestone 1 Connectivity Active"}
