# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

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

    @api.model
    def get_app_permissions(self):
        """Backend-driven App Permission Resolution"""
        apps_config = [
            {"id": "sale", "name": "Sales (sale.order)", "model": "sale.order", "icon": "fa-shopping-cart", "active": True},
            {"id": "account", "name": "Invoicing & Accounting (account.move)", "model": "account.move", "icon": "fa-calculator", "active": True},
            {"id": "stock", "name": "Inventory & Warehouses (stock.picking)", "model": "stock.picking", "icon": "fa-cubes", "active": True},
            {"id": "crm", "name": "CRM & Opportunities (crm.lead)", "model": "crm.lead", "icon": "fa-handshake-o", "active": True},
            {"id": "partner", "name": "Contacts & Customers (res.partner)", "model": "res.partner", "icon": "fa-address-book", "active": True},
            {"id": "hr", "name": "Employees & HR (hr.employee)", "model": "hr.employee", "icon": "fa-users", "active": False},
            {"id": "purchase", "name": "Purchase Orders (purchase.order)", "model": "purchase.order", "icon": "fa-truck", "active": True},
            {"id": "project", "name": "Projects & Tasks (project.task)", "model": "project.task", "icon": "fa-tasks", "active": True},
        ]
        
        result = []
        for app in apps_config:
            model_rec = self.env['ir.model'].sudo().search([('model', '=', app['model'])], limit=1)
            rule = None
            if model_rec:
                rule = self.sudo().search([('model_id', '=', model_rec.id)], limit=1)
            
            result.append({
                "id": app["id"],
                "name": app["name"],
                "icon": app["icon"],
                "read": rule.allow_read if rule else True,
                "create": rule.allow_create if rule else False,
                "write": rule.allow_write if rule else False,
                "delete": rule.allow_unlink if rule else False,
                "active": rule.active if rule else app["active"]
            })
        return result

    @api.model
    def update_app_permission(self, app_id, perm, state):
        """Update Read, Create, Write, or Delete permission in backend DB"""
        app_models = {
            "sale": "sale.order",
            "account": "account.move",
            "stock": "stock.picking",
            "crm": "crm.lead",
            "partner": "res.partner",
            "hr": "hr.employee",
            "purchase": "purchase.order",
            "project": "project.task"
        }
        target_model_name = app_models.get(app_id)
        if not target_model_name:
            return False

        perm_field_map = {
            'read': 'allow_read',
            'create': 'allow_create',
            'write': 'allow_write',
            'delete': 'allow_unlink'
        }
        target_field = perm_field_map.get(perm)
        if not target_field:
            return False

        model_rec = self.env['ir.model'].sudo().search([('model', '=', target_model_name)], limit=1)
        if model_rec:
            rule = self.sudo().search([('model_id', '=', model_rec.id)], limit=1)
            if rule:
                rule.sudo().write({target_field: bool(state)})
            else:
                vals = {
                    'model_id': model_rec.id,
                    'allow_read': True,
                    'allow_create': False,
                    'allow_write': False,
                    'allow_unlink': False
                }
                vals[target_field] = bool(state)
                self.sudo().create(vals)
        return True

    @api.model
    def update_app_read_permission(self, app_id, read_state):
        """Backward-compatible wrapper for updating Read permission"""
        return self.update_app_permission(app_id, 'read', read_state)

    @api.model
    def check_permission(self, model_name, operation):
        """
        Validate backend CRUD permission for a target model and operation.
        Returns True if allowed, False if denied.
        """
        if not model_name:
            return True
        try:
            model_rec = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
            if not model_rec:
                return True
            rule = self.sudo().search([('model_id', '=', model_rec.id), ('active', '=', True)], limit=1)
            if not rule:
                if operation in ['read', 'search', 'aggregate', 'explain']:
                    return True
                return False

            if operation == 'create':
                return rule.allow_create
            elif operation in ['write', 'update']:
                return rule.allow_write
            elif operation in ['delete', 'unlink']:
                return rule.allow_unlink
            elif operation in ['read', 'search', 'aggregate', 'explain']:
                return rule.allow_read
            return True
        except Exception as e:
            _logger.error(f"Error checking permission for {model_name}: {e}")
            return True
