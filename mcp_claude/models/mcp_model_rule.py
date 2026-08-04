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
            model_rec = self.env['ir.model'].search([('model', '=', app['model'])], limit=1)
            rule = None
            if model_rec:
                rule = self.search([('model_id', '=', model_rec.id)], limit=1)
            
            result.append({
                "id": app["id"],
                "name": app["name"],
                "icon": app["icon"],
                "read": rule.allow_read if rule else True,
                "create": False,
                "write": False,
                "delete": False,
                "active": rule.active if rule else app["active"]
            })
        return result

    @api.model
    def update_app_read_permission(self, app_id, read_state):
        """Update Read permission in backend DB"""
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
        if target_model_name:
            model_rec = self.env['ir.model'].search([('model', '=', target_model_name)], limit=1)
            if model_rec:
                rule = self.search([('model_id', '=', model_rec.id)], limit=1)
                if rule:
                    super(MCPModelRule, rule).write({'allow_read': bool(read_state)})
                else:
                    super(MCPModelRule, self).create({
                        'model_id': model_rec.id,
                        'allow_read': bool(read_state),
                        'allow_create': False,
                        'allow_write': False,
                        'allow_unlink': False
                    })
        return True
