# -*- coding: utf-8 -*-
import json
import re
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

ALLOWED_OPERATIONS = ['search', 'read', 'aggregate', 'explain']
FORBIDDEN_KEYWORDS = ['create', 'write', 'update', 'delete', 'unlink', 'remove', 'drop', 'execute', 'alter']

class MCPTool(models.Model):
    _name = 'mcp.tool'
    _description = 'MCP Registered Tool'
    _order = 'sequence, name'

    name = fields.Char(string="Tool Technical Name", required=True, index=True)
    display_name = fields.Char(string="Display Name", required=True)
    description = fields.Text(string="Description", required=True)
    model_name = fields.Char(string="Target Odoo Model", required=True, index=True)
    operation = fields.Selection([
        ('search', 'Search'),
        ('read', 'Read'),
        ('aggregate', 'Aggregate'),
        ('explain', 'Explain')
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

    @api.constrains('name', 'operation', 'model_name')
    def _check_tool_validity(self):
        for tool in self:
            # 1. Technical Name Validation
            if not tool.name or not re.match(r'^[a-z0-9_]+$', tool.name):
                raise ValidationError(_("Tool name '%s' is invalid! Technical name must contain only lowercase letters, digits, and underscores.") % tool.name)
            
            # Check forbidden mutation keywords in tool name
            for kw in FORBIDDEN_KEYWORDS:
                if kw in tool.name.lower():
                    raise ValidationError(_("Tool name cannot contain mutation verb '%s'. Only read-only operations are supported.") % kw)

            # 2. Strict Read-Only Operation Validation
            if tool.operation not in ALLOWED_OPERATIONS:
                raise ValidationError(_("Operation '%s' is not allowed. Only search, read, aggregate, and explain are supported.") % tool.operation)

            # 3. Model Existence Check
            if tool.model_name not in self.env:
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
            raise UserError(_("Operation not allowed: %s. This MCP deployment is configured for read-only access.") % op)

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
