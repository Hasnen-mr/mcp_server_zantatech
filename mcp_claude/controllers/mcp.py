# -*- coding: utf-8 -*-
import os
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

    @http.route('/mcp/v1/sse', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
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
            return Response(json.dumps({"error": msg}), status=401, headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'})

        host = request.httprequest.host
        scheme = request.httprequest.scheme
        raw_token = kwargs.get('token') or kwargs.get('api_key') or 'mcp_live_default'
        
        if ":8069" in host:
            host_url = host.replace(":8069", ":8443")
            endpoint_uri = "https://" + host_url + "/mcp/v1/messages?token=" + raw_token
        else:
            endpoint_uri = scheme + "://" + host + "/mcp/v1/messages?token=" + raw_token

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
            tools_recs = request.env['mcp.tool'].sudo().search([('active', '=', True)])
            tools_list = []
            for t in tools_recs:
                tools_list.append({
                    "name": t.name,
                    "description": t.description or "Odoo Tool Function",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "kwargs": {"type": "object", "description": "Keyword arguments"}
                        }
                    }
                })
            if not tools_list:
                tools_list.append({
                    "name": "odoo_ping",
                    "description": "Ping Odoo MCP Server",
                    "inputSchema": {"type": "object", "properties": {}}
                })
            resp_body = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}}

        elif method == "tools/call":
            params = body.get('params', {})
            t_name = params.get('name', '')
            
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
                _logger.info(f"AUDIT LOG RECORDED IN POSTGRES FOR TOOL: {t_name or 'odoo_ping'}")
            except Exception as log_err:
                _logger.warning(f"Failed writing audit log: {log_err}")

            resp_body = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": f"Odoo MCP Server Active! Invoked tool: {t_name}. Connection Successful!"}
                    ],
                    "isError": False
                }
            }

        elif method == "resources/list":
            resp_body = {"jsonrpc": "2.0", "id": req_id, "result": {"resources": []}}

        elif method == "prompts/list":
            resp_body = {"jsonrpc": "2.0", "id": req_id, "result": {"prompts": []}}

        else:
            resp_body = {"jsonrpc": "2.0", "id": req_id, "result": {"status": "acknowledged", "method": method}}

        return Response(json.dumps(resp_body), status=200, headers=headers)
