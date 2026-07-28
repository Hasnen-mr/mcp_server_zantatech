# -*- coding: utf-8 -*-
from odoo import models, fields

class MCPModelRule(models.Model):
    _name = 'mcp.model.rule'
    _description = 'MCP Model Permission Rule'

    model_id = fields.Many2one('ir.model', string="Target Model", required=True, ondelete='cascade')
    allow_read = fields.Boolean(string="Allow Read", default=True)
    allow_create = fields.Boolean(string="Allow Create", default=False)
    allow_write = fields.Boolean(string="Allow Update", default=False)
    allow_unlink = fields.Boolean(string="Allow Delete", default=False)
    allow_call_method = fields.Boolean(string="Allow Method Calls", default=False)
    active = fields.Boolean(string="Active", default=True)
