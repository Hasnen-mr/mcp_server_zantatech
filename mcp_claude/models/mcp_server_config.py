import logging
_logger = logging.getLogger(__name__)
from odoo.addons.mcp_claude.bin.mcp_https_proxy import start_proxy_thread
# -*- coding: utf-8 -*-
from odoo import models, fields

class MCPServerConfig(models.Model):
    def _register_hook(self):
        res = super()._register_hook()
        try:
            active_port = start_proxy_thread()
            if active_port:
                _logger.info(f"MCP Trusted HTTPS Proxy Started Automatically on Port {active_port}")
        except Exception as e:
            _logger.warning(f"HTTPS Proxy auto-start notice: {e}")
        return res

    _name = 'mcp.server.config'
    _description = 'MCP Server Configuration'

    name = fields.Char(string="Configuration Name", default="Default MCP Settings", required=True)
    profile = fields.Selection([
        ('development', 'Development'),
        ('testing', 'Testing'),
        ('production', 'Production')
    ], string="Configuration Profile", default='development', required=True)

    enable_tools = fields.Boolean(string="Enable Tools", default=True)
    enable_resources = fields.Boolean(string="Enable Resources", default=True)
    enable_prompts = fields.Boolean(string="Enable Prompts", default=False)
    enable_oauth = fields.Boolean(string="Enable OAuth 2.0", default=True)
    enable_api_keys = fields.Boolean(string="Enable API Keys", default=True)

    default_token_ttl = fields.Integer(string="Token TTL (Seconds)", default=3600)
    rate_limit_rpm = fields.Integer(string="Max Requests Per Minute", default=120)
