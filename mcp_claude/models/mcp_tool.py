# -*- coding: utf-8 -*-
import json
import re
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

ALLOWED_OPERATIONS = ['search', 'read', 'aggregate', 'explain', 'create', 'write', 'delete']

class MCPTool(models.Model):
    _name = 'mcp.tool'
    _description = 'MCP Registered Tool'
    _order = 'sequence, name'

    name = fields.Char(string="Tool Technical Name", required=True, index=True)
    display_name = fields.Char(string="Display Name")
    description = fields.Text(string="Description")
    model_name = fields.Char(string="Target Odoo Model", index=True)
    operation = fields.Selection([
        ('search', 'Search'),
        ('read', 'Read'),
        ('aggregate', 'Aggregate'),
        ('explain', 'Explain'),
        ('create', 'Create'),
        ('write', 'Update'),
        ('delete', 'Delete')
    ], string="Operation", default='search', required=True)
    search_fields = fields.Text(string="Search Fields (JSON)", default="[]")
    result_fields = fields.Text(string="Result Fields (JSON)", default="[]")
    active = fields.Boolean(string="Active", default=True)
    is_builtin = fields.Boolean(string="Is Built-in Tool", default=False, readonly=True)
    sequence = fields.Integer(string="Sequence", default=10)
    version = fields.Char(string="Version", default="1.0.0")
    requires_approval = fields.Boolean(string="Requires Human Approval", default=False)
    category = fields.Selection([
        ('crm', 'CRM'),
        ('sales', 'Sales'),
        ('inventory', 'Inventory'),
        ('accounting', 'Accounting'),
        ('contacts', 'Contacts'),
        ('technical', 'Technical / System')
    ], string="Category", default='technical', required=True)
    risk_level = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk')
    ], string="Risk Level", default='low', required=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Tool technical name must be unique!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('display_name') and vals.get('name'):
                vals['display_name'] = vals['name'].replace('_', ' ').title()
        return super().create(vals_list)

    @api.constrains('name', 'operation', 'model_name')
    def _check_tool_validity(self):
        for tool in self:
            # 1. Technical Name Validation
            if not tool.name or not re.match(r'^[a-z0-9_]+$', tool.name):
                raise ValidationError(_("Tool name '%s' is invalid! Technical name must contain only lowercase letters, digits, and underscores.") % tool.name)

            # 2. Operation Validation
            if tool.operation not in ALLOWED_OPERATIONS:
                raise ValidationError(_("Operation '%s' is not allowed.") % tool.operation)

            # 3. Model Existence Check — only for custom tools with a model_name set
            if not tool.is_builtin and tool.model_name and tool.model_name not in self.env:
                raise ValidationError(_("Model '%s' does not exist in this Odoo instance.") % tool.model_name)

    @api.model
    def get_available_models(self):
        """Fetch list of active installed Odoo models for Control Center UI selector."""
        models_recs = self.env['ir.model'].sudo().search([('transient', '=', False)], order='name')
        result = []
        for m in models_recs:
            if m.model in self.env:
                result.append({
                    'model': m.model,
                    'name': m.name or m.model
                })
        return result

    @api.model
    def get_model_fields(self, model_name):
        """Fetch fields metadata for target Odoo model."""
        if not model_name or model_name not in self.env:
            return []
        
        try:
            fields_meta = self.env[model_name].sudo().fields_get()
            result = []
            for fname, finfo in fields_meta.items():
                # Filter out binary or internal password fields
                if finfo.get('type') in ['binary', 'reference']:
                    continue
                result.append({
                    'name': fname,
                    'label': finfo.get('string', fname),
                    'type': finfo.get('type', 'char'),
                    'readonly': finfo.get('readonly', False),
                    'required': finfo.get('required', False),
                    'relation': finfo.get('relation', ''),
                    'searchable': finfo.get('searchable', True),
                    'stored': finfo.get('store', True)
                })
            result.sort(key=lambda x: x['name'])
            return result
        except Exception as e:
            _logger.error(f"Error fetching fields for model {model_name}: {e}")
            return []

    @api.model
    def action_create_custom_tool(self, values):
        """Create custom dynamic tool with validation and audit logging."""
        op = values.get('operation', 'search')
        if op not in ALLOWED_OPERATIONS:
            raise UserError(_("Operation not allowed: %s.") % op)

        name = (values.get('name') or '').strip().lower()
        if not name or not re.match(r'^[a-z0-9_]+$', name):
            raise UserError(_("Invalid tool technical name. Must be lowercase alphanumeric with underscores."))

        existing = self.sudo().search([('name', '=', name)], limit=1)
        if existing:
            raise UserError(_("A tool with technical name '%s' already exists.") % name)

        search_fields = values.get('search_fields', [])
        result_fields = values.get('result_fields', [])

        tool = self.sudo().create({
            'name': name,
            'display_name': values.get('display_name') or name,
            'description': values.get('description') or f"Search Odoo {values.get('model_name')}",
            'model_name': values.get('model_name'),
            'operation': op,
            'search_fields': json.dumps(search_fields) if isinstance(search_fields, list) else search_fields,
            'result_fields': json.dumps(result_fields) if isinstance(result_fields, list) else result_fields,
            'active': True,
            'is_builtin': False,
            'sequence': 10
        })

        # Audit Log
        self.env['mcp.audit.log'].sudo().create({
            'user_id': self.env.user.id or 1,
            'tool_name': tool.name,
            'model_name': tool.model_name,
            'action_type': 'tool_created',
            'status': 'success',
            'request_payload': json.dumps(values)
        })

        return tool.id

    @api.model
    def action_update_custom_tool(self, tool_id, values):
        """Update existing custom tool."""
        tool = self.sudo().browse(tool_id)
        if not tool.exists():
            raise UserError(_("Tool not found."))

        # Operation type cannot be changed after creation
        if 'operation' in values and values['operation'] != tool.operation:
            raise UserError(_("Operation type cannot be changed after creation."))

        search_fields = values.get('search_fields')
        result_fields = values.get('result_fields')

        update_dict = {}
        if 'display_name' in values:
            update_dict['display_name'] = values['display_name']
        if 'description' in values:
            update_dict['description'] = values['description']
        if search_fields is not None:
            update_dict['search_fields'] = json.dumps(search_fields) if isinstance(search_fields, list) else search_fields
        if result_fields is not None:
            update_dict['result_fields'] = json.dumps(result_fields) if isinstance(result_fields, list) else result_fields
        if 'sequence' in values:
            update_dict['sequence'] = values['sequence']
        if 'active' in values:
            update_dict['active'] = values['active']

        tool.write(update_dict)

        # Audit Log
        self.env['mcp.audit.log'].sudo().create({
            'user_id': self.env.user.id or 1,
            'tool_name': tool.name,
            'model_name': tool.model_name,
            'action_type': 'tool_updated',
            'status': 'success',
            'request_payload': json.dumps(update_dict)
        })

        return True

    @api.model
    def action_delete_custom_tool(self, tool_id):
        """Delete custom tool. Built-in tools cannot be deleted."""
        tool = self.sudo().browse(tool_id)
        if not tool.exists():
            return True
        if tool.is_builtin:
            raise UserError(_("Built-in tools cannot be deleted."))

        tool_name = tool.name
        model_name = tool.model_name

        tool.unlink()

        # Audit Log
        self.env['mcp.audit.log'].sudo().create({
            'user_id': self.env.user.id or 1,
            'tool_name': tool_name,
            'model_name': model_name,
            'action_type': 'tool_deleted',
            'status': 'success'
        })
        return True

    @api.model
    def action_toggle_tool_active(self, tool_id):
        """Toggle active state of a tool."""
        tool = self.sudo().browse(tool_id)
        if not tool.exists():
            return False
        
        new_state = not tool.active
        tool.write({'active': new_state})

        # Audit Log
        self.env['mcp.audit.log'].sudo().create({
            'user_id': self.env.user.id or 1,
            'tool_name': tool.name,
            'model_name': tool.model_name,
            'action_type': 'tool_enabled' if new_state else 'tool_disabled',
            'status': 'success'
        })
        return new_state

    @api.model
    def get_environment_info(self, override_url=None):
        """
        Dynamically inspect deployment environment based on current request URL or web.base.url.
        Classifies as Local Development, Production Server (HTTPS), or Remote HTTP.
        Supports Nginx / Apache / Cloudflare reverse proxies with forwarded header awareness.
        """
        import urllib.parse
        import ipaddress

        req = self.env.get('request') if hasattr(self.env, 'get') else None
        
        # 1. Determine Base URL & Scheme with Request Priority and Reverse Proxy Awareness
        base_url = None
        scheme = None

        if override_url:
            base_url = str(override_url).strip()
        elif req and hasattr(req, 'httprequest') and req.httprequest:
            httpreq = req.httprequest
            # Inspect X-Forwarded-Proto and X-Forwarded-Host from reverse proxy (Nginx / Cloudflare)
            forwarded_proto = httpreq.headers.get('X-Forwarded-Proto') or httpreq.headers.get('X-Forwarded-Scheme')
            forwarded_host = httpreq.headers.get('X-Forwarded-Host')

            if forwarded_proto:
                scheme = forwarded_proto.split(',')[0].strip().lower()
            elif httpreq.is_secure or httpreq.scheme == 'https':
                scheme = 'https'
            else:
                scheme = (httpreq.scheme or 'http').lower()

            if forwarded_host:
                host_str = forwarded_host.split(',')[0].strip()
                base_url = f"{scheme}://{host_str}"
            else:
                host_url = getattr(httpreq, 'host_url', None) or getattr(httpreq, 'url_root', None)
                if host_url:
                    base_url = host_url

        if not base_url:
            # Fallback to web.base.url config parameter if no active HTTP request exists
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or "http://localhost:8069"

        # Normalize Base URL (no trailing slashes, ensure scheme)
        base_url = base_url.rstrip('/')
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'http://' + base_url

        parsed = urllib.parse.urlparse(base_url)
        if not scheme:
            scheme = (parsed.scheme or 'http').lower()
        hostname = (parsed.hostname or 'localhost').lower()
        port = parsed.port or (443 if scheme == 'https' else 80)

        # 2. Localhost & Private IP Subnet Detection
        is_localhost = False
        if hostname in ['localhost', '127.0.0.1', '0.0.0.0', '::1'] or hostname.endswith('.local'):
            is_localhost = True
        else:
            try:
                ip_obj = ipaddress.ip_address(hostname)
                if ip_obj.is_private or ip_obj.is_loopback:
                    is_localhost = True
            except ValueError:
                # String hostname checks for local domain suffixes or private IP subnets
                if hostname.startswith(('10.', '192.168.')):
                    is_localhost = True
                elif hostname.startswith('172.'):
                    parts = hostname.split('.')
                    if len(parts) >= 2 and parts[1].isdigit():
                        octet2 = int(parts[1])
                        if 16 <= octet2 <= 31:
                            is_localhost = True

        is_https = (scheme == 'https')

        # 3. Environment Classification & Recommendation Rules
        if is_localhost:
            env_code = "local"
            env_title = "Local Development"
            recommended = "json"
            supports_direct = False
            badge_label = "🔵 Local Development"
            badge_class = "bg-info"
            status_text = "🔵 Local Development"
            reason = "This server is only accessible locally."
            warning_message = None
        elif is_https:
            env_code = "production"
            env_title = "Production Server"
            recommended = "url"
            supports_direct = True
            badge_label = "🟢 HTTPS Enabled"
            badge_class = "bg-success"
            status_text = "🟢 HTTPS Enabled"
            reason = "HTTPS is enabled. Claude Desktop can securely connect directly."
            warning_message = None
        else:
            env_code = "remote-http"
            env_title = "Remote Server"
            recommended = "json"
            supports_direct = False
            badge_label = "🟡 HTTPS Recommended"
            badge_class = "bg-warning text-dark"
            status_text = "🟡 HTTPS Recommended"
            reason = "HTTPS is required for direct URL connections."
            warning_message = "This server is publicly accessible but is not using HTTPS. Claude Desktop direct URL connections require HTTPS. Enable HTTPS before exposing this server."

        # Direct URL (normalized path without double slashes)
        direct_url = f"{base_url}/mcp"

        # Fetch system parameters for JSON generation
        wizard_params = self.get_wizard_config_params()
        python_exec = wizard_params["python_path"]
        bridge_script = wizard_params["bridge_path"]
        api_key_val = wizard_params["api_key"]

        # Dynamically generate JSON config using system parameters and detected base_url
        args_list = [bridge_script, "--server", base_url]
        if api_key_val:
            args_list.extend(["--api-key", api_key_val])

        config_dict = {
            "mcpServers": {
                "odoo": {
                    "command": python_exec,
                    "args": args_list
                }
            }
        }
        config_json_str = json.dumps(config_dict, indent=2)

        # Build fully ordered connection_methods list
        url_method = {
            "id": "url",
            "title": "Direct URL Connection",
            "recommended": (recommended == "url"),
            "badge": "✅ Recommended" if (recommended == "url") else "Requires HTTPS Remote Domain",
            "supports_direct_url": supports_direct,
            "url": direct_url,
            "description": "Connect Claude Desktop directly over HTTPS to Odoo without local proxy scripts."
        }

        json_method = {
            "id": "json",
            "title": "Claude Desktop JSON Configuration",
            "recommended": (recommended == "json"),
            "badge": "✅ Recommended" if (recommended == "json") else "Alternative Option",
            "config_json": config_json_str,
            "description": "Stdio bridge configuration snippet for claude_desktop_config.json."
        }

        if recommended == "url":
            connection_methods = [url_method, json_method]
        else:
            connection_methods = [json_method, url_method]

        # Connection Status Live Diagnostics
        has_oauth = ('mcp.oauth.client' in self.env)

        import os

        # Check Python path & Bridge path configuration status
        is_python_default = (python_exec == "python")
        is_bridge_default = (bridge_script == "mcp_bridge.py")

        python_valid = bool(python_exec and not is_python_default)
        bridge_valid = bool(bridge_script and not is_bridge_default)

        # For localhost deployments, verify local filesystem existence if custom path provided
        if is_localhost:
            if python_valid and not os.path.exists(python_exec):
                python_status_state = "invalid"
                python_status_text = f"🔴 Path Not Found: {python_exec}"
            elif python_valid:
                python_status_state = "configured"
                python_status_text = "🟢 Configured & Verified"
            else:
                python_status_state = "missing"
                python_status_text = "🟡 Not Configured (Set Absolute Path)"

            if bridge_valid and not os.path.exists(bridge_script):
                bridge_status_state = "invalid"
                bridge_status_text = f"🔴 Script Not Found: {bridge_script}"
            elif bridge_valid:
                bridge_status_state = "configured"
                bridge_status_text = "🟢 Configured & Verified"
            else:
                bridge_status_state = "missing"
                bridge_status_text = "🟡 Not Configured (Set Absolute Path)"
        else:
            # Production: check if value is set without checking server OS filesystem
            python_status_state = "configured" if python_valid else "missing"
            python_status_text = "🟢 Configured" if python_valid else "🟡 Not Configured (Set Absolute Path)"
            bridge_status_state = "configured" if bridge_valid else "missing"
            bridge_status_text = "🟢 Configured" if bridge_valid else "🟡 Not Configured (Set Absolute Path)"

        # Validation object with detailed status states
        validation = {
            "base_url": {
                "state": "configured" if base_url else "invalid",
                "text": "🟢 Detected" if base_url else "🔴 Not Detected",
                "val": base_url
            },
            "https": {
                "state": "configured" if is_https else "missing",
                "text": "🟢 Enabled" if is_https else "🟡 HTTP Only (HTTPS Recommended)",
                "enabled": is_https
            },
            "direct_url": {
                "state": "configured" if supports_direct else "missing",
                "text": "🟢 Supported" if supports_direct else "⚪ Stdio Bridge Only",
                "supported": supports_direct
            },
            "python_path": {
                "state": python_status_state,
                "text": python_status_text,
                "val": python_exec,
                "is_configured": python_valid
            },
            "bridge_path": {
                "state": bridge_status_state,
                "text": bridge_status_text,
                "val": bridge_script,
                "is_configured": bridge_valid
            },
            "api_key": {
                "state": "configured" if api_key_val else "missing",
                "text": "🟢 Configured" if api_key_val else "🟡 Default Key",
                "val": api_key_val
            },
            "is_json_valid": bool(python_valid and bridge_valid),
            "missing_json_reason": None if (python_valid and bridge_valid) else (
                "Python executable is not configured. Configure the absolute Python executable path in Administrator Settings before using Claude Desktop JSON Configuration." if not python_valid else
                "MCP bridge script path is not configured. Configure the absolute bridge script path in Administrator Settings before using Claude Desktop JSON Configuration."
            )
        }

        claude_compatibility = {
            "status": "Compatible",
            "badge": "🟢 Compatible",
            "capabilities": [
                { "name": "OAuth 2.1 Authentication", "supported": True, "note": "RFC 6749 / PKCE supported" },
                { "name": "MCP Protocol Version 2024-11-05", "supported": True, "note": "Official spec compliant" },
                { "name": "Streamable HTTP & SSE Transport", "supported": True, "note": "Real-time streaming enabled" },
                { "name": "Direct URL Connection", "supported": supports_direct, "note": "Available on HTTPS production domains" if supports_direct else "Requires HTTPS on remote deployment" }
            ]
        }

        connection_status = {
            "server_reachability": {
                "label": "Server Reachability",
                "status": "Online",
                "ok": True,
                "badge": "🟢 Online"
            },
            "mcp_endpoint": {
                "label": "MCP Endpoint",
                "status": "Reachable",
                "ok": True,
                "badge": "🟢 Reachable"
            },
            "oauth_support": {
                "label": "OAuth Support",
                "status": "Detected" if has_oauth else "Not Detected",
                "ok": has_oauth,
                "badge": "🟢 Detected" if has_oauth else "⚪ Not Detected"
            },
            "recommended_connection": {
                "label": "Recommended Connection",
                "status": "Direct URL Connection" if (recommended == "url") else "Claude Desktop JSON Configuration",
                "code": recommended,
                "ok": True,
                "badge": "🌐 Direct URL" if (recommended == "url") else "📄 Stdio JSON"
            }
        }

        return {
            "environment": env_code,
            "environment_title": env_title,
            "base_url": base_url,
            "hostname": hostname,
            "scheme": scheme,
            "port": port,
            "is_https": is_https,
            "is_localhost": is_localhost,
            "recommended_connection": recommended,
            "supports_direct_url": supports_direct,
            "badge_label": badge_label,
            "badge_class": badge_class,
            "status_text": status_text,
            "reason": reason,
            "warning_message": warning_message,
            "direct_url": direct_url,
            "config_json": config_json_str,
            "connection_methods": connection_methods,
            "connection_status": connection_status,
            "validation": validation,
            "wizard_params": wizard_params,
            "claude_compatibility": claude_compatibility
        }

    @api.model
    def get_wizard_config_params(self):
        """Fetch system configuration parameters for Claude Desktop JSON generation."""
        ICPSudo = self.env["ir.config_parameter"].sudo()
        return {
            "python_path": ICPSudo.get_param("mcp_claude.python_path") or "python",
            "bridge_path": ICPSudo.get_param("mcp_claude.bridge_path") or "mcp_bridge.py",
            "api_key": ICPSudo.get_param("mcp_claude.default_api_key") or "mcp_live_default",
            "server_url_override": ICPSudo.get_param("mcp_claude.server_url") or "",
        }

    @api.model
    def set_wizard_config_params(self, python_path=None, bridge_path=None, api_key=None, server_url=None):
        """Save system configuration parameters for Claude Desktop JSON generation."""
        ICPSudo = self.env["ir.config_parameter"].sudo()
        if python_path is not None:
            ICPSudo.set_param("mcp_claude.python_path", str(python_path).strip())
        if bridge_path is not None:
            ICPSudo.set_param("mcp_claude.bridge_path", str(bridge_path).strip())
        if api_key is not None:
            ICPSudo.set_param("mcp_claude.default_api_key", str(api_key).strip())
        if server_url is not None:
            ICPSudo.set_param("mcp_claude.server_url", str(server_url).strip())
        return self.get_environment_info()

