# -*- coding: utf-8 -*-
from odoo import models, fields

class MCPSession(models.Model):
    _name = 'mcp.session'
    _description = 'MCP Client Session'

    session_token = fields.Char(string="Session Token", required=True)
    user_id = fields.Many2one('res.users', string="User", required=True)
    client_name = fields.Char(string="Client Application", default="Claude Desktop")
    expires_at = fields.Datetime(string="Expires At", required=True)
    active = fields.Boolean(string="Active Session", default=True)
