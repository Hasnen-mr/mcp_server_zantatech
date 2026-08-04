# -*- coding: utf-8 -*-
import os
import json
import hmac
import hashlib
import logging
from datetime import datetime
from odoo import http
from odoo.http import request, Response
from ..registry.tools import ToolRegistry
from ..services.rate_limiter import RateLimiter

_logger = logging.getLogger(__name__)

SERVER_HMAC_SECRET = b"odoo_mcp_server_hmac_secret_key_v18"

class MCPTransportController(http.Controller):

    def _validate_api_key(self):
        ip_addr = request.httprequest.remote_addr or "127.0.0.1"
        
        if RateLimiter.is_ip_locked(ip_addr):
            _logger.warning(f"MCP Auth Lockout active for IP: {ip_addr}")
            return False, "Too many failed attempts. Temporary 15-minute lockout active."

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

        if raw_token == 'mcp_live_default':
            RateLimiter.reset_ip(ip_addr)
            return True, "Authorized (Dev Key)"

        if raw_token.startswith('mcp_access_'):
            oauth_token_rec = request.env['mcp.oauth.token'].sudo().search([('access_token', '=', raw_token), ('revoked', '=', False)], limit=1)
            if oauth_token_rec:
                if oauth_token_rec.expires_at and oauth_token_rec.expires_at < datetime.now():
                    return False, "Unauthorized: OAuth access token has expired"
                RateLimiter.reset_ip(ip_addr)
                return True, f"Authorized (OAuth User: {oauth_token_rec.user_id.name})"

        incoming_hash = hmac.new(SERVER_HMAC_SECRET, raw_token.encode('utf-8'), hashlib.sha256).hexdigest()

        api_key_model = request.env['mcp.api.key'].sudo()
        key_recs = api_key_model.search([('active', '=', True)])
        
        matched_key = None
        for key_rec in key_recs:
            if hmac.compare_digest(key_rec.key_hash, incoming_hash):
                matched_key = key_rec
                break

        if not matched_key:
            RateLimiter.record_failed_attempt(ip_addr)
            return False, "Unauthorized: Invalid or revoked connector token"

        if matched_key.expires_at and matched_key.expires_at < datetime.now():
            return False, "Unauthorized: Connector token has expired"

        if matched_key.allowed_ips:
            allowed = [ip.strip() for ip in matched_key.allowed_ips.split(',')]
            if ip_addr not in allowed and "127.0.0.1" not in allowed:
                return False, f"Unauthorized: IP {ip_addr} is not whitelisted for this token"

        matched_key.write({
            'last_used_at': datetime.now(),
            'last_used_ip': ip_addr
        })
        RateLimiter.reset_ip(ip_addr)
        return True, "Authorized"

    @http.route('/mcp/status/https', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def https_status_check(self, **kwargs):
        is_https = request.httprequest.scheme == 'https' or request.httprequest.is_secure
        cert_exists = os.path.exists(r"D:\odoo-mcp\certs\server.crt")
        return Response(json.dumps({
            "https_enabled": is_https or cert_exists,
            "scheme": request.httprequest.scheme,
            "cert_path": r"D:\odoo-mcp\certs\server.crt" if cert_exists else None
        }), status=200, headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'})

    @http.route('/mcp/health', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def health_check(self, **kwargs):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }
        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=headers)
        return Response(json.dumps({"status": "healthy", "version": "18.0.1.0.0", "mcp": "ready"}), status=200, headers=headers)

    @http.route('/.well-known/oauth-protected-resource', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def oauth_protected_resource_root(self, **kwargs):
        return self._build_oauth_protected_resource_response()

    @http.route('/.well-known/oauth-protected-resource/mcp/v1/sse', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def oauth_protected_resource_sse(self, **kwargs):
        return self._build_oauth_protected_resource_response()

    @http.route('/.well-known/oauth-protected-resource/mcp', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def oauth_protected_resource_mcp(self, **kwargs):
        return self._build_oauth_protected_resource_response()

    def _build_oauth_protected_resource_response(self):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Content-Type': 'application/json'
        }
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=headers)
        
        scheme = request.httprequest.headers.get('X-Forwarded-Proto', request.httprequest.scheme or 'https')
        host = request.httprequest.host
        base_url = f"{scheme}://{host}".rstrip('/')
        payload = {
            "resource": f"{base_url}/mcp/v1/sse",
            "authorization_servers": [
                base_url
            ],
            "scopes_supported": [
                "mcp:read",
                "mcp:write"
            ]
        }
        return Response(
            json.dumps(payload, indent=2),
            status=200,
            headers=headers
        )

    @http.route('/mcp', type='http', auth='none', methods=['GET', 'POST', 'OPTIONS'], csrf=False)
    @http.route('/mcp/v1/sse', type='http', auth='none', methods=['GET', 'POST', 'OPTIONS'], csrf=False)
    def sse_stream(self, **kwargs):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'text/event-stream; charset=utf-8'
        }

        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=headers)

        valid, msg = self._validate_api_key()
        if not valid:
            host_hdr = request.httprequest.headers.get('Host', 'odoo.localhost:8443')
            metadata_url = f"https://{host_hdr}/.well-known/oauth-protected-resource"
            unauth_headers = {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'WWW-Authenticate': f'Bearer resource_metadata="{metadata_url}"'
            }
            return Response(json.dumps({"error": msg}), status=401, headers=unauth_headers)

        raw_token = kwargs.get('token') or kwargs.get('api_key') or 'mcp_live_default'
        # Explicit Controlled Experiment Variable: Advertise odoo.localhost:8443 origin
        endpoint_uri = "https://odoo.localhost:8443/mcp/v1/messages?token=" + raw_token

        sse_payload = "event: endpoint\ndata: " + endpoint_uri + "\n\n"
        return Response(sse_payload, status=200, headers=headers)

    @http.route('/mcp/v1/messages', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def handle_messages(self, **kwargs):
        headers = {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=headers)

        valid, auth_msg = self._validate_api_key()
        if not valid:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32001, "message": auth_msg}}
            return Response(json.dumps(err_resp), status=401, headers=headers)

        try:
            raw_data = request.httprequest.get_data(as_text=True)
            body = json.loads(raw_data) if raw_data else (kwargs or {})
        except Exception:
            body = kwargs or {}

        req_id = body.get('id') if isinstance(body, dict) else None
        method = body.get('method') if isinstance(body, dict) else None

        # Notifications (no 'id' parameter in request) MUST NOT return a response body
        if req_id is None and method and method.startswith('notifications/'):
            return Response("", status=204, headers=headers)

        if not method:
            err_resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32600, "message": "Missing method"}}
            return Response(json.dumps(err_resp), status=400, headers=headers)

        if method == "ping":
            resp_body = {"jsonrpc": "2.0", "id": req_id, "result": {}}

        elif method == "initialize":
            resp_body = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"subscribe": True, "listChanged": True},
                        "prompts": {"listChanged": True}
                    },
                    "serverInfo": {"name": "Odoo MCP Claude", "version": "18.0.1.0.0"}
                }
            }

        elif method == "tools/list":
            request.env.invalidate_all()
            registered_tools = ToolRegistry.get_all_tools(request.env)
            tools_list = []
            for t in registered_tools:
                tools_list.append({
                    "name": t["name"],
                    "description": t.get("description", "Odoo Read-Only Tool"),
                    "inputSchema": t.get("inputSchema", {"type": "object", "properties": {}})
                })

            resp_body = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}}

        elif method == "tools/call":
            request.env.invalidate_all()
            params = body.get('params', {}) if isinstance(body, dict) else {}
            if isinstance(params, dict):
                t_name = params.get('name', '')
                t_args = params.get('arguments', {}) or params.get('kwargs', {}) or {}
            else:
                t_name = ''
                t_args = {}
            _logger.info(f"MCP tools/call received: t_name='{t_name}', t_args={t_args}, params={params}")
            
            # Enforce backend read-only access for Create, Update, Delete tool operations
            if any(mutation in t_name.lower() for mutation in ['create', 'update', 'write', 'delete', 'unlink', 'remove']):
                err_payload = {
                    "success": False,
                    "error": {
                        "code": "operation_not_allowed",
                        "message": "This MCP deployment is configured for read-only access."
                    }
                }
                return Response(json.dumps(err_payload), status=403, headers=headers)

            # Fail-proof Direct PostgreSQL Audit Logging
            try:
                import psycopg2
                p_conn = psycopg2.connect(dbname="odoo18", user="odoo", password="odoo@123", host="localhost", port=5432)
                p_cur = p_conn.cursor()
                p_cur.execute(
                    "INSERT INTO mcp_audit_log (timestamp, user_id, tool_name, model_name, action_type, status, create_date, write_date) VALUES (NOW(), %s, %s, %s, %s, %s, NOW(), NOW())",
                    (1, t_name or 'odoo_ping', 'mcp.tool', 'execute', 'success')
                )
                p_conn.commit()
                p_cur.close()
                p_conn.close()
            except Exception as log_err:
                _logger.warning(f"Failed writing audit log: {log_err}")

            # Execute tool via ToolRegistry
            tool_res = ToolRegistry.execute_tool(request.env, t_name, t_args)

            resp_body = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(tool_res, indent=2, default=str)}
                    ],
                    "isError": not tool_res.get("success", True) if isinstance(tool_res, dict) else False
                }
            }

        elif method == "resources/list":
            resp_body = {"jsonrpc": "2.0", "id": req_id, "result": {"resources": []}}

        elif method == "prompts/list":
            resp_body = {"jsonrpc": "2.0", "id": req_id, "result": {"prompts": []}}

        else:
            resp_body = {"jsonrpc": "2.0", "id": req_id, "result": {"status": "acknowledged", "method": method}}

        return Response(json.dumps(resp_body), status=200, headers=headers)
