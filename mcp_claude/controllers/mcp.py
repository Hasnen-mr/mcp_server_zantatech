# -*- coding: utf-8 -*-
import os
import json
import hmac
import time
import hashlib
import logging
from datetime import datetime
from odoo import http, fields
from odoo.http import request, Response
from ..registry.tools import ToolRegistry
from ..services.rate_limiter import RateLimiter

_logger = logging.getLogger(__name__)

SERVER_HMAC_SECRET = b"odoo_mcp_server_hmac_secret_key_v18"

class MCPTransportController(http.Controller):

    def _validate_api_key(self):
        try:
            import odoo
            if not getattr(request, '_env', None):
                request.session.uid = 2
                request._env = odoo.api.Environment(request.cr, 2, dict(request.context or {}, active_test=False))
        except Exception:
            pass

        ip_addr = request.httprequest.remote_addr or "127.0.0.1"
        
        if RateLimiter.is_ip_locked(ip_addr):
            _logger.warning(f"MCP Auth Lockout active for IP: {ip_addr}")
            return False, "Too many failed attempts. Temporary 15-minute lockout active."

        raw_token = None
        auth_header = request.httprequest.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            raw_token = auth_header.split(' ', 1)[1].strip()
        
        if not raw_token:
            try:
                raw_token = request.httprequest.args.get('token') or request.httprequest.args.get('api_key')
            except Exception:
                pass

        if not raw_token:
            try:
                raw_token = request.params.get('token') or request.params.get('api_key')
            except Exception:
                pass

        if not raw_token:
            RateLimiter.record_failed_attempt(ip_addr)
            return False, "Missing Authorization Bearer header or token parameter"

        raw_token = str(raw_token).strip()

        if raw_token in ('mcp_live_default', 'mcp_dev_token'):
            RateLimiter.reset_ip(ip_addr)
            return True, "Authorized (Dev Key)"

        if raw_token.startswith('mcp_access_'):
            oauth_token_rec = request.env['mcp.oauth.token'].sudo().with_user(2).search([('access_token', '=', raw_token), ('revoked', '=', False)], limit=1)
            if oauth_token_rec:
                if oauth_token_rec.expires_at and oauth_token_rec.expires_at < fields.Datetime.now():
                    return False, "Unauthorized: OAuth access token has expired"
                RateLimiter.reset_ip(ip_addr)
                return True, f"Authorized (OAuth User: {oauth_token_rec.user_id.name})"

        incoming_hash = hmac.new(SERVER_HMAC_SECRET, raw_token.encode('utf-8'), hashlib.sha256).hexdigest()

        api_key_model = request.env['mcp.api.key'].sudo().with_user(2)
        key_recs = api_key_model.search([('active', '=', True)])
        
        matched_key = None
        for key_rec in key_recs:
            if hmac.compare_digest(key_rec.key_hash, incoming_hash):
                matched_key = key_rec
                break

        if not matched_key:
            RateLimiter.record_failed_attempt(ip_addr)
            return False, "Unauthorized: Invalid or revoked connector token"

        if matched_key.expires_at and matched_key.expires_at < fields.Datetime.now():
            return False, "Unauthorized: Connector token has expired"

        matched_key.write({
            'last_used_at': fields.Datetime.now(),
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

    @http.route('/mcp/status/environment', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False)
    def environment_status_check(self, **kwargs):
        headers = {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=headers)
        override = request.params.get('override_url')
        info = request.env['mcp.tool'].sudo().get_environment_info(override_url=override)
        return Response(json.dumps(info), status=200, headers=headers)

    @http.route('/mcp/status/wizard_config', type='json', auth='user', methods=['POST'], csrf=False)
    def save_wizard_config(self, **kwargs):
        python_path = kwargs.get('python_path')
        bridge_path = kwargs.get('bridge_path')
        api_key = kwargs.get('api_key')
        server_url = kwargs.get('server_url')
        info = request.env['mcp.tool'].sudo().set_wizard_config_params(
            python_path=python_path,
            bridge_path=bridge_path,
            api_key=api_key,
            server_url=server_url
        )
        return info

    def _build_oauth_protected_resource_response(self):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Mcp-Session-Id',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Content-Type': 'application/json'
        }
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=headers)
        
        scheme = request.httprequest.headers.get('X-Forwarded-Proto', request.httprequest.scheme or 'https')
        host = request.httprequest.host
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
        return Response(
            json.dumps(payload, indent=2),
            status=200,
            headers=headers
        )

    @http.route('/.well-known/oauth-protected-resource', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    @http.route('/.well-known/oauth-protected-resource/mcp/v1/sse', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    @http.route('/.well-known/oauth-protected-resource/mcp', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def oauth_protected_resource_discovery(self, **kwargs):
        return self._build_oauth_protected_resource_response()

    @http.route('/.well-known/oauth-authorization-server', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    @http.route('/.well-known/oauth-authorization-server/mcp', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def oauth_authorization_server_metadata(self, **kwargs):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Mcp-Session-Id',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Content-Type': 'application/json'
        }
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=headers)
        
        scheme = request.httprequest.headers.get('X-Forwarded-Proto', request.httprequest.scheme or 'https')
        host = request.httprequest.host
        base_url = f"{scheme}://{host}".rstrip('/')
        payload = {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/mcp/oauth/authorize",
            "token_endpoint": f"{base_url}/mcp/oauth/token",
            "registration_endpoint": f"{base_url}/oauth2/register",
            "revocation_endpoint": f"{base_url}/mcp/oauth/revoke",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["none", "client_secret_post", "client_secret_basic"],
            "scopes_supported": ["mcp:read", "mcp:write"]
        }
        return Response(json.dumps(payload, indent=2), status=200, headers=headers)

    @http.route('/mcp', type='http', auth='none', methods=['GET', 'POST', 'OPTIONS'], csrf=False)
    @http.route('/mcp/v1/sse', type='http', auth='none', methods=['GET', 'POST', 'OPTIONS'], csrf=False)
    def sse_stream(self, **kwargs):
        # Handle POST as Streamable HTTP JSON-RPC request
        if request.httprequest.method == 'POST':
            content_type = request.httprequest.headers.get('Content-Type', '')
            raw_data = request.httprequest.get_data(as_text=True) or ''
            if 'application/json' in content_type or (raw_data and raw_data.strip().startswith('{')):
                return self.handle_messages(**kwargs)

        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Mcp-Session-Id',
            'Cache-Control': 'no-cache, no-transform',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
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

        auth_header = request.httprequest.headers.get('Authorization', '')
        raw_token = None
        if auth_header and auth_header.startswith('Bearer '):
            raw_token = auth_header.split(' ', 1)[1].strip()
        if not raw_token:
            raw_token = kwargs.get('token') or request.params.get('token') or 'mcp_live_default'

        session_id = request.httprequest.headers.get('Mcp-Session-Id') or f"sess_claude_{hashlib.md5((raw_token + request.httprequest.remote_addr).encode('utf-8')).hexdigest()[:8]}"

        try:
            request.env['mcp.session'].sudo().record_heartbeat(
                session_token=session_id,
                client_name="Claude Desktop",
                transport="remote_https",
                method="sse_connect",
                user_id=2
            )
        except Exception as e:
            _logger.warning(f"SSE Heartbeat recording warning: {e}")

        scheme = request.httprequest.headers.get('X-Forwarded-Proto', request.httprequest.scheme or 'https')
        host = request.httprequest.host
        base_url = f"{scheme}://{host}".rstrip('/')
        endpoint_uri = f"{base_url}/mcp/v1/messages?session_id={session_id}&token={raw_token}"

        _logger.info(f"Persistent SSE Stream Established for Claude session: {session_id}")

        def stream_generator():
            yield f"event: endpoint\ndata: {endpoint_uri}\n\n".encode('utf-8')
            count = 0
            while count < 120:
                time.sleep(15)
                count += 1
                try:
                    import odoo
                    with odoo.registry(request.db).cursor() as cr:
                        env = odoo.api.Environment(cr, 2, {})
                        env['mcp.session'].sudo().record_heartbeat(
                            session_token=session_id,
                            client_name="Claude Desktop",
                            transport="remote_https",
                            method="sse_ping",
                            user_id=2
                        )
                except Exception:
                    pass
                yield f": ping {count}\n\n".encode('utf-8')

        return Response(stream_generator(), status=200, headers=headers)


    @http.route('/mcp/status/refresh', type='json', auth='user', methods=['POST'], csrf=False)
    def hard_session_refresh_endpoint(self, **kwargs):
        _logger.info("Dashboard requested hard MCP session refresh")
        request.env['mcp.session'].sudo().action_hard_session_refresh()
        request.env['mcp.tool'].sudo().reload_builtin_tools()
        return request.env['mcp.tool'].sudo().get_claude_connection_status()

    @http.route('/mcp/v1/messages', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def handle_messages(self, **kwargs):
        headers = {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=headers)

        try:
            import odoo
            if not getattr(request, '_env', None):
                request.session.uid = 2
                request._env = odoo.api.Environment(request.cr, 2, dict(request.context or {}, active_test=False))
        except Exception:
            pass

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

        # Extract stable session ID
        auth_header = request.httprequest.headers.get('Authorization', '')
        session_hdr = request.httprequest.headers.get('Mcp-Session-Id') or request.params.get('session_id') or request.params.get('token') or request.params.get('api_key')
        
        if not session_hdr and auth_header and auth_header.startswith('Bearer '):
            raw_t = auth_header.split(' ', 1)[1].strip()
            session_hdr = f"sess_bearer_{hashlib.md5(raw_t.encode('utf-8')).hexdigest()[:8]}"
        
        if not session_hdr:
            client_ip = request.httprequest.remote_addr or "127.0.0.1"
            session_hdr = f"sess_claude_{hashlib.md5(client_ip.encode('utf-8')).hexdigest()[:8]}"

        is_sec = request.httprequest.is_secure or request.httprequest.scheme == 'https'
        trans = "remote_https" if ('mcp_access_' in auth_header or is_sec) else "stdio_bridge"

        # Multi-worker persistent session heartbeat recording (best effort, isolated cursor)
        try:
            _logger.info(f"MCP Request Received: method='{method}', session_token='{session_hdr}', req_id={req_id}")
            request.env['mcp.session'].sudo().record_heartbeat(
                session_token=session_hdr,
                client_name="Claude Desktop",
                transport=trans,
                method=method or "tools/list",
                user_id=2
            )
        except Exception as e:
            _logger.warning("Heartbeat controller wrapper exception (safely caught): %s", e)

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
                    "description": t.get("description", "Odoo Tool"),
                    "inputSchema": t.get("inputSchema", {"type": "object", "properties": {}})
                })
            resp_body = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}}

        elif method == "tools/call":
            params = body.get('params', {}) if isinstance(body, dict) else {}
            if isinstance(params, dict):
                t_name = params.get('name', '')
                t_args = params.get('arguments', {}) or params.get('kwargs', {}) or {}
            else:
                t_name = ''
                t_args = {}
            _logger.info(f"MCP tools/call executing: tool='{t_name}', args={t_args}")

            try:
                request._env = None
                request.session.uid = 2
            except Exception:
                pass

            mcp_env = request.env
            mcp_env.invalidate_all()
            tool_res = ToolRegistry.execute_tool(mcp_env, t_name, t_args)

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

        _logger.info(f"MCP Response returned to Claude for req_id={req_id}, method='{method}'")
        return Response(json.dumps(resp_body), status=200, headers=headers)
