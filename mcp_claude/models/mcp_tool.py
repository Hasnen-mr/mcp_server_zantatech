# -*- coding: utf-8 -*-
from odoo import models, fields

class MCPTool(models.Model):
    _name = 'mcp.tool'
    _description = 'MCP Registered Tool'

    name = fields.Char(string="Tool Technical Name", required=True)
    version = fields.Char(string="Version", default="1.0.0", required=True)
    category = fields.Selection([
        ('crm', 'CRM'),
        ('sales', 'Sales'),
        ('inventory', 'Inventory'),
        ('accounting', 'Accounting'),
        ('projects', 'Projects'),
        ('hr', 'Human Resources'),
        ('technical', 'Technical / System')
    ], string="Category", default='technical', required=True)
    description = fields.Text(string="Description")
    risk_level = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk')
    ], string="Risk Level", default='low', required=True)
    requires_approval = fields.Boolean(string="Requires Human Approval", default=False)
    active = fields.Boolean(string="Active", default=True)
