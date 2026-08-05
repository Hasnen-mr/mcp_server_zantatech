# -*- coding: utf-8 -*-
import json
import logging
from typing import Dict, Any, List, Callable

_logger = logging.getLogger(__name__)
_REGISTERED_TOOLS: Dict[str, Dict[str, Any]] = {}

def mcp_tool(name: str, version: str = "1.0.0", category: str = "General",
             description: str = "", risk_level: str = "Low",
             read_only: bool = True, requires_approval: bool = False, author: str = "Core",
             input_schema: Dict[str, Any] = None):
    def decorator(func: Callable):
        tool_meta = {
            "name": name,
            "version": version,
            "category": category,
            "description": description or func.__doc__ or "",
            "risk_level": risk_level,
            "read_only": read_only,
            "requires_approval": requires_approval,
            "author": author,
            "inputSchema": input_schema or {"type": "object", "properties": {}},
            "handler": func,
            "is_builtin": True
        }
        _REGISTERED_TOOLS[name] = tool_meta
        return func
    return decorator

class ToolRegistry:
    @classmethod
    def generate_input_schema(cls, operation: str, search_fields: list) -> dict:
        """Dynamically generate MCP inputSchema based on operation and configured fields."""
        if operation == "create":
            props = {}
            if search_fields:
                for sf in search_fields:
                    props[sf] = {"type": "string", "description": f"Value for {sf}"}
            return {
                "type": "object",
                "properties": {
                    "values": {
                        "type": "object",
                        "properties": props,
                        "description": "Field values to create the record"
                    }
                },
                "required": ["values"]
            }
        elif operation == "write":
            props = {}
            if search_fields:
                for sf in search_fields:
                    props[sf] = {"type": "string", "description": f"Value for {sf}"}
            return {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Target record ID"},
                    "values": {
                        "type": "object",
                        "properties": props,
                        "description": "Field values to update"
                    }
                },
                "required": ["id", "values"]
            }
        elif operation == "delete":
            return {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Target record ID to delete"}
                },
                "required": ["id"]
            }
        elif operation == "explain":
            return {
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Target Odoo model name"},
                    "id": {"type": "integer", "description": "Optional record ID"}
                },
                "required": ["model"]
            }
        elif operation == "read":
            return {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Target record ID"},
                    "fields": {"type": "array", "items": {"type": "string"}, "description": "Optional fields list to read"}
                },
                "required": ["id"]
            }
        elif operation == "aggregate":
            return {
                "type": "object",
                "properties": {
                    "domain": {"type": "array", "description": "Search domain filters"},
                    "groupby": {"type": "array", "items": {"type": "string"}, "description": "Group by dimensions"},
                    "fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to aggregate"}
                }
            }
        else: # search
            props = {
                "limit": {"type": "integer", "default": 20, "description": "Max records to return (1-100)"},
                "offset": {"type": "integer", "default": 0, "description": "Pagination offset"}
            }
            if search_fields:
                for sf in search_fields:
                    props[sf] = {"type": "string", "description": f"Filter by {sf}"}
            return {
                "type": "object",
                "properties": props
            }

    @classmethod
    def get_all_tools(cls, env=None) -> List[Dict[str, Any]]:
        """Return unified list of built-in Python tools and active database custom tools."""
        tools_list = []
        # 1. Built-in Tools
        for name, tool_meta in _REGISTERED_TOOLS.items():
            tools_list.append({
                "id": f"builtin_{name}",
                "name": tool_meta["name"],
                "description": tool_meta.get("description", ""),
                "category": tool_meta.get("category", "General"),
                "inputSchema": tool_meta.get("inputSchema", {"type": "object", "properties": {}}),
                "is_builtin": True,
                "active": True
            })

        # 2. Database Custom Tools (if env provided)
        if env:
            try:
                db_tools = env['mcp.tool'].sudo().search([('active', '=', True)], order='sequence, id')
                builtin_names = {t["name"] for t in tools_list}
                for db_t in db_tools:
                    if db_t.name not in builtin_names:
                        s_fields = json.loads(db_t.search_fields) if db_t.search_fields else []
                        tools_list.append({
                            "id": db_t.id,
                            "name": db_t.name,
                            "display_name": db_t.display_name or db_t.name,
                            "description": db_t.description or f"{db_t.operation.capitalize()} {db_t.model_name}",
                            "model_name": db_t.model_name,
                            "operation": db_t.operation,
                            "search_fields": s_fields,
                            "result_fields": json.loads(db_t.result_fields) if db_t.result_fields else [],
                            "inputSchema": cls.generate_input_schema(db_t.operation, s_fields),
                            "is_builtin": False,
                            "active": db_t.active
                        })
            except Exception as e:
                _logger.warning(f"Failed fetching database custom tools: {e}")

        return tools_list

    @classmethod
    def get_tool(cls, env, name: str) -> Dict[str, Any]:
        if name in _REGISTERED_TOOLS:
            return _REGISTERED_TOOLS[name]

        if env:
            name_clean = (name or '').strip().lower()
            all_tools = cls.get_all_tools(env)
            for t in all_tools:
                if (t.get('name') or '').strip().lower() == name_clean:
                    return t

            db_t = env['mcp.tool'].sudo().with_context(active_test=False).search([('name', '=', name_clean)], limit=1)
            if db_t:
                s_fields = json.loads(db_t.search_fields) if db_t.search_fields else []
                r_fields = json.loads(db_t.result_fields) if db_t.result_fields else []
                return {
                    "id": db_t.id,
                    "name": db_t.name,
                    "display_name": db_t.display_name,
                    "description": db_t.description,
                    "model_name": db_t.model_name,
                    "operation": db_t.operation,
                    "search_fields": s_fields,
                    "result_fields": r_fields,
                    "inputSchema": cls.generate_input_schema(db_t.operation, s_fields),
                    "is_builtin": False,
                    "active": db_t.active
                }
        return None

    @classmethod
    def execute_tool(cls, env, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            admin_user = env['res.users'].sudo().search([('id', '=', 2)], limit=1)
            if not admin_user:
                admin_user = env['res.users'].sudo().search([], limit=1)
            if admin_user:
                env = env.with_user(admin_user)
        except Exception:
            pass
        # 1. Check Built-in Tools
        if name in _REGISTERED_TOOLS:
            tool_meta = _REGISTERED_TOOLS[name]
            handler = tool_meta.get('handler')
            if not handler:
                return {"success": False, "error": {"code": "missing_handler", "message": f"Handler for '{name}' missing."}}
            try:
                return handler(env, params or {})
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                _logger.error(f"Error executing built-in tool '{name}': {e}\n{tb}")
                return {"success": False, "error": {"code": "execution_error", "message": str(e), "traceback": tb}}

        # 2. Check Database Custom Tools
        tool_meta = cls.get_tool(env, name)
        if not tool_meta:
            return {
                "success": False,
                "error": {
                    "code": "unknown_tool",
                    "message": f"MCP Tool '{name}' is not registered or is disabled."
                }
            }

        model_name = tool_meta.get("model_name")
        operation = tool_meta.get("operation")
        search_fields = tool_meta.get("search_fields", [])
        result_fields = tool_meta.get("result_fields", [])

        if not model_name or model_name not in env:
            return {"success": False, "error": {"code": "unknown_model", "message": f"Model '{model_name}' not found."}}

        try:
            model_obj = env[model_name].sudo()

            if operation == "search":
                if not env['mcp.model.rule'].check_permission(model_name, 'search'):
                    return {"success": False, "error": {"code": "access_denied", "message": f"Read permission is disabled for model '{model_name}'."}}
                domain = []
                if params and search_fields:
                    for sf in search_fields:
                        val = params.get(sf)
                        if val:
                            domain.append((sf, 'ilike', val))
                limit = min(max(int(params.get('limit', 20) if params else 20), 1), 100)
                offset = max(int(params.get('offset', 0) if params else 0), 0)

                read_f = result_fields if result_fields else None
                records = model_obj.search_read(domain, fields=read_f, limit=limit, offset=offset)
                return {"success": True, "count": len(records), "records": records}

            elif operation == "read":
                if not env['mcp.model.rule'].check_permission(model_name, 'read'):
                    return {"success": False, "error": {"code": "access_denied", "message": f"Read permission is disabled for model '{model_name}'."}}
                rec_id = params.get('id') if params else None
                if not rec_id:
                    return {"success": False, "error": {"code": "missing_id", "message": "Record ID is required for read operation."}}
                rec = model_obj.browse(rec_id)
                if not rec.exists():
                    return {"success": False, "error": {"code": "record_not_found", "message": f"Record #{rec_id} not found."}}
                read_f = result_fields if result_fields else (params.get('fields') if params else None)
                data = rec.read(read_f)[0]
                cleaned = {}
                for k, v in data.items():
                    if isinstance(v, (bytes, bytearray)):
                        cleaned[k] = "<binary_data>"
                    else:
                        cleaned[k] = v
                return {"success": True, "id": rec_id, "data": cleaned}

            elif operation == "create":
                if not env['mcp.model.rule'].check_permission(model_name, 'create'):
                    return {"success": False, "error": {"code": "access_denied", "message": f"Create permission is disabled for model '{model_name}'."}}
                vals = params.get('values') or {}
                if not isinstance(vals, dict) or not vals:
                    return {"success": False, "error": {"code": "missing_values", "message": "Field values object is required for create operation."}}
                rec = model_obj.create(vals)
                return {"success": True, "id": rec.id, "display_name": rec.display_name}

            elif operation == "write":
                if not env['mcp.model.rule'].check_permission(model_name, 'write'):
                    return {"success": False, "error": {"code": "access_denied", "message": f"Update permission is disabled for model '{model_name}'."}}
                rec_id = params.get('id')
                vals = params.get('values') or {}
                if not rec_id:
                    return {"success": False, "error": {"code": "missing_id", "message": "Record ID is required for write operation."}}
                rec = model_obj.browse(rec_id)
                if not rec.exists():
                    return {"success": False, "error": {"code": "record_not_found", "message": f"Record #{rec_id} not found."}}
                rec.write(vals)
                return {"success": True, "id": rec_id, "updated_fields": list(vals.keys())}

            elif operation == "delete":
                if not env['mcp.model.rule'].check_permission(model_name, 'delete'):
                    return {"success": False, "error": {"code": "access_denied", "message": f"Delete permission is disabled for model '{model_name}'."}}
                rec_id = params.get('id')
                if not rec_id:
                    return {"success": False, "error": {"code": "missing_id", "message": "Record ID is required for delete operation."}}
                rec = model_obj.browse(rec_id)
                if not rec.exists():
                    return {"success": False, "error": {"code": "record_not_found", "message": f"Record #{rec_id} not found."}}
                rec.unlink()
                return {"success": True, "deleted_id": rec_id}

            elif operation == "aggregate":
                if not env['mcp.model.rule'].check_permission(model_name, 'read'):
                    return {"success": False, "error": {"code": "access_denied", "message": f"Read permission is disabled for model '{model_name}'."}}
                domain = params.get('domain', []) if params else []
                groupby = params.get('groupby', []) if params else []
                fields_agg = params.get('fields', []) if params else (result_fields or [])
                res = model_obj.read_group(domain=domain, fields=fields_agg, groupby=groupby)
                return {"success": True, "results": res}

            elif operation == "explain":
                if not env['mcp.model.rule'].check_permission(model_name, 'read'):
                    return {"success": False, "error": {"code": "access_denied", "message": f"Read permission is disabled for model '{model_name}'."}}
                field_info = model_obj.fields_get()
                rec_id = params.get('id') if params else None
                disp_name = model_obj.browse(rec_id).display_name if rec_id and model_obj.browse(rec_id).exists() else ""
                meta = {
                    "model": model_name,
                    "display_name": disp_name,
                    "field_count": len(field_info),
                    "fields": {}
                }
                for fname, fmeta in field_info.items():
                    if not result_fields or fname in result_fields:
                        meta["fields"][fname] = {
                            "label": fmeta.get("string", ""),
                            "type": fmeta.get("type", ""),
                            "relation": fmeta.get("relation", ""),
                            "required": fmeta.get("required", False),
                            "readonly": fmeta.get("readonly", False)
                        }
                return {"success": True, "meta": meta}

            else:
                return {"success": False, "error": {"code": "operation_not_allowed", "message": f"Operation '{operation}' not supported."}}

        except Exception as e:
            env.cr.rollback()
            import traceback
            tb_str = traceback.format_exc()
            _logger.error(f"Error in odoo_create_record for {model_name}: {e}\n{tb_str}")
            return {"success": False, "error": {"code": "orm_error", "message": str(e), "traceback": tb_str}}


# ==============================================================================
# READ-ONLY BUILT-IN TOOL IMPLEMENTATIONS
# ==============================================================================

@mcp_tool(
    name="odoo_ping",
    description="Ping Odoo MCP Server to verify connection status",
    read_only=True,
    input_schema={"type": "object", "properties": {}}
)
def handle_odoo_ping(env, params):
    return {"status": "online", "message": "Odoo MCP Server is active and operational."}


@mcp_tool(
    name="odoo_search_partners",
    description="Search Odoo Contacts & Customers (res.partner). Filter by name, email, phone, or company.",
    category="Contacts",
    read_only=True,
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Filter by partner or display name"},
            "email": {"type": "string", "description": "Filter by email address"},
            "phone": {"type": "string", "description": "Filter by phone or mobile number"},
            "company": {"type": "string", "description": "Filter by company name"},
            "limit": {"type": "integer", "default": 20, "description": "Max records to return (1-100)"},
            "offset": {"type": "integer", "default": 0, "description": "Pagination offset"}
        }
    }
)
def handle_search_partners(env, params):
    if 'res.partner' not in env:
        return {"success": True, "count": 0, "records": []}
    domain = []
    if params.get('name'):
        domain.append('|')
        domain.append(('name', 'ilike', params['name']))
        domain.append(('display_name', 'ilike', params['name']))
    if params.get('email'):
        domain.append(('email', 'ilike', params['email']))
    if params.get('phone'):
        domain.append('|')
        domain.append(('phone', 'ilike', params['phone']))
        domain.append(('mobile', 'ilike', params['phone']))
    if params.get('company'):
        domain.append('|')
        domain.append(('parent_id.name', 'ilike', params['company']))
        domain.append(('company_name', 'ilike', params['company']))

    limit = min(max(int(params.get('limit', 20)), 1), 100)
    offset = max(int(params.get('offset', 0)), 0)

    partners = env['res.partner'].sudo().search(domain, limit=limit, offset=offset)
    records = []
    for p in partners:
        records.append({
            "id": p.id,
            "name": p.name or "",
            "email": p.email or "",
            "phone": p.phone or "",
            "mobile": p.mobile or "",
            "company": p.parent_id.name if p.parent_id else (p.company_name or "")
        })
    return {"success": True, "count": len(records), "records": records}


@mcp_tool(
    name="odoo_search_leads",
    description="Search Odoo CRM Leads & Opportunities (crm.lead). Filter by name, partner, stage, or salesperson.",
    category="CRM",
    read_only=True,
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Filter by opportunity title"},
            "partner": {"type": "string", "description": "Filter by customer/contact name"},
            "stage": {"type": "string", "description": "Filter by stage name"},
            "salesperson": {"type": "string", "description": "Filter by assigned salesperson"},
            "limit": {"type": "integer", "default": 20, "description": "Max records to return (1-100)"},
            "offset": {"type": "integer", "default": 0, "description": "Pagination offset"}
        }
    }
)
def handle_search_leads(env, params):
    if 'crm.lead' not in env:
        return {"success": True, "count": 0, "records": [], "note": "CRM module not installed"}
    domain = []
    if params.get('name'):
        domain.append(('name', 'ilike', params['name']))
    if params.get('partner'):
        domain.append('|')
        domain.append(('partner_id.name', 'ilike', params['partner']))
        domain.append(('contact_name', 'ilike', params['partner']))
    if params.get('stage'):
        domain.append(('stage_id.name', 'ilike', params['stage']))
    if params.get('salesperson'):
        domain.append(('user_id.name', 'ilike', params['salesperson']))

    limit = min(max(int(params.get('limit', 20)), 1), 100)
    offset = max(int(params.get('offset', 0)), 0)

    leads = env['crm.lead'].sudo().search(domain, limit=limit, offset=offset)
    records = []
    for l in leads:
        records.append({
            "id": l.id,
            "name": l.name or "",
            "partner": l.partner_id.name if l.partner_id else (l.contact_name or ""),
            "stage": l.stage_id.name if l.stage_id else "",
            "expected_revenue": getattr(l, 'expected_revenue', 0.0) or 0.0,
            "probability": getattr(l, 'probability', 0.0) or 0.0
        })
    return {"success": True, "count": len(records), "records": records}


@mcp_tool(
    name="odoo_search_orders",
    description="Search Odoo Sales Orders (sale.order). Filter by customer, state, or date range.",
    category="Sales",
    read_only=True,
    input_schema={
        "type": "object",
        "properties": {
            "customer": {"type": "string", "description": "Filter by customer name"},
            "state": {"type": "string", "description": "Filter by state (draft, sent, sale, done, cancel)"},
            "date_from": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "date_to": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "limit": {"type": "integer", "default": 20, "description": "Max records to return (1-100)"},
            "offset": {"type": "integer", "default": 0, "description": "Pagination offset"}
        }
    }
)
def handle_search_orders(env, params):
    if 'sale.order' not in env:
        return {"success": True, "count": 0, "records": [], "note": "Sales module not installed"}
    domain = []
    if params.get('customer'):
        domain.append(('partner_id.name', 'ilike', params['customer']))
    if params.get('state'):
        domain.append(('state', '=', params['state']))
    if params.get('date_from'):
        domain.append(('date_order', '>=', params['date_from']))
    if params.get('date_to'):
        domain.append(('date_order', '<=', params['date_to']))

    limit = min(max(int(params.get('limit', 20)), 1), 100)
    offset = max(int(params.get('offset', 0)), 0)

    orders = env['sale.order'].sudo().search(domain, limit=limit, offset=offset)
    records = []
    for s in orders:
        records.append({
            "id": s.id,
            "name": s.name or "",
            "customer": s.partner_id.name if s.partner_id else "",
            "date": str(s.date_order) if s.date_order else "",
            "state": s.state or "",
            "amount_total": s.amount_total or 0.0
        })
    return {"success": True, "count": len(records), "records": records}


@mcp_tool(
    name="odoo_search_invoices",
    description="Search Odoo Customer Invoices (account.move). Filter by customer, state, payment state, or date range.",
    category="Accounting",
    read_only=True,
    input_schema={
        "type": "object",
        "properties": {
            "customer": {"type": "string", "description": "Filter by customer name"},
            "state": {"type": "string", "description": "Filter by state (draft, posted, cancel)"},
            "payment_state": {"type": "string", "description": "Filter by payment state (not_paid, in_payment, paid, partial)"},
            "date_from": {"type": "string", "description": "Invoice start date (YYYY-MM-DD)"},
            "date_to": {"type": "string", "description": "Invoice end date (YYYY-MM-DD)"},
            "limit": {"type": "integer", "default": 20, "description": "Max records to return (1-100)"},
            "offset": {"type": "integer", "default": 0, "description": "Pagination offset"}
        }
    }
)
def handle_search_invoices(env, params):
    if 'account.move' not in env:
        return {"success": True, "count": 0, "records": [], "note": "Accounting module not installed"}
    domain = [('move_type', 'in', ['out_invoice', 'out_refund'])]
    if params.get('customer'):
        domain.append(('partner_id.name', 'ilike', params['customer']))
    if params.get('state'):
        domain.append(('state', '=', params['state']))
    if params.get('payment_state'):
        domain.append(('payment_state', '=', params['payment_state']))
    if params.get('date_from'):
        domain.append(('invoice_date', '>=', params['date_from']))
    if params.get('date_to'):
        domain.append(('invoice_date', '<=', params['date_to']))

    limit = min(max(int(params.get('limit', 20)), 1), 100)
    offset = max(int(params.get('offset', 0)), 0)

    invoices = env['account.move'].sudo().search(domain, limit=limit, offset=offset)
    records = []
    for i in invoices:
        records.append({
            "id": i.id,
            "number": i.name or "",
            "partner": i.partner_id.name if i.partner_id else "",
            "date": str(i.invoice_date) if i.invoice_date else "",
            "due_date": str(i.invoice_date_due) if i.invoice_date_due else "",
            "state": i.state or "",
            "payment_state": getattr(i, 'payment_state', '') or "",
            "amount_total": i.amount_total or 0.0
        })
    return {"success": True, "count": len(records), "records": records}


@mcp_tool(
    name="odoo_search_products",
    description="Search Odoo Products (product.product). Filter by name, internal reference, barcode, or category.",
    category="Inventory",
    read_only=True,
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Filter by product name"},
            "internal_reference": {"type": "string", "description": "Filter by default code / SKU"},
            "barcode": {"type": "string", "description": "Filter by barcode"},
            "category": {"type": "string", "description": "Filter by category name"},
            "limit": {"type": "integer", "default": 20, "description": "Max records to return (1-100)"},
            "offset": {"type": "integer", "default": 0, "description": "Pagination offset"}
        }
    }
)
def handle_search_products(env, params):
    if 'product.product' not in env:
        return {"success": True, "count": 0, "records": [], "note": "Product module not installed"}
    domain = []
    if params.get('name'):
        domain.append(('name', 'ilike', params['name']))
    if params.get('internal_reference'):
        domain.append(('default_code', 'ilike', params['internal_reference']))
    if params.get('barcode'):
        domain.append(('barcode', 'ilike', params['barcode']))
    if params.get('category'):
        domain.append(('categ_id.name', 'ilike', params['category']))

    limit = min(max(int(params.get('limit', 20)), 1), 100)
    offset = max(int(params.get('offset', 0)), 0)

    products = env['product.product'].sudo().search(domain, limit=limit, offset=offset)
    records = []
    for pr in products:
        records.append({
            "id": pr.id,
            "name": pr.name or "",
            "default_code": pr.default_code or "",
            "barcode": pr.barcode or "",
            "list_price": pr.list_price or 0.0,
            "qty_available": getattr(pr, 'qty_available', 0.0) or 0.0,
            "category": pr.categ_id.name if pr.categ_id else ""
        })
    return {"success": True, "count": len(records), "records": records}


@mcp_tool(
    name="odoo_read_record",
    description="Generic Read Tool to fetch specific field values for a target record by ID.",
    category="Generic Read",
    read_only=True,
    input_schema={
        "type": "object",
        "properties": {
            "model": {"type": "string", "description": "Target Odoo model name (e.g. sale.order, res.partner)"},
            "id": {"type": "integer", "description": "Target record ID"},
            "fields": {"type": "array", "items": {"type": "string"}, "description": "List of field names to read"}
        },
        "required": ["model", "id"]
    }
)
def handle_read_record(env, params):
    model_name = params.get('model')
    rec_id = params.get('id')
    fields = params.get('fields')

    if not model_name or model_name not in env:
        return {"success": False, "error": {"code": "unknown_model", "message": f"Model '{model_name}' does not exist."}}

    record = env[model_name].sudo().browse(rec_id)
    if not record.exists():
        return {"success": False, "error": {"code": "record_not_found", "message": f"Record #{rec_id} not found on model '{model_name}'."}}

    res = record.read(fields)[0] if fields else record.read()[0]
    cleaned = {}
    for k, v in res.items():
        if isinstance(v, (bytes, bytearray)):
            cleaned[k] = "<binary_data>"
        else:
            cleaned[k] = v
    return {"success": True, "model": model_name, "id": rec_id, "data": cleaned}


@mcp_tool(
    name="odoo_aggregate",
    description="Compute aggregation (count, sum, average, min, max) on Odoo models using ORM read_group().",
    category="Analytics",
    read_only=True,
    input_schema={
        "type": "object",
        "properties": {
            "model": {"type": "string", "description": "Target Odoo model name"},
            "domain": {"type": "array", "description": "Search domain filters"},
            "groupby": {"type": "array", "items": {"type": "string"}, "description": "Fields to group by"},
            "fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to aggregate (e.g. ['amount_total:sum'])"},
            "operation": {"type": "string", "description": "Operation type: count, sum, average, minimum, maximum"}
        },
        "required": ["model", "fields"]
    }
)
def handle_aggregate(env, params):
    model_name = params.get('model')
    domain = params.get('domain', [])
    groupby = params.get('groupby', [])
    fields = params.get('fields', [])

    if not model_name or model_name not in env:
        return {"success": False, "error": {"code": "unknown_model", "message": f"Model '{model_name}' does not exist."}}

    try:
        res = env[model_name].sudo().read_group(domain=domain, fields=fields, groupby=groupby)
        return {"success": True, "model": model_name, "results": res}
    except Exception as e:
        return {"success": False, "error": {"code": "invalid_parameters", "message": str(e)}}


@mcp_tool(
    name="odoo_explain_record",
    description="Explain the field structure, labels, types, and relations of any Odoo model for AI inspection.",
    category="Meta",
    read_only=True,
    input_schema={
        "type": "object",
        "properties": {
            "model": {"type": "string", "description": "Target Odoo model name (e.g. sale.order, res.partner)"},
            "id": {"type": "integer", "description": "Optional record ID to include display_name"}
        },
        "required": ["model"]
    }
)
def handle_explain_record(env, params):
    model_name = params.get('model')
    rec_id = params.get('id')

    if not model_name or model_name not in env:
        return {"success": False, "error": {"code": "unknown_model", "message": f"Model '{model_name}' does not exist."}}

    model_obj = env[model_name].sudo()
    field_info = model_obj.fields_get()

    display_name = ""
    if rec_id:
        rec = model_obj.browse(rec_id)
        if rec.exists():
            display_name = rec.display_name

    meta = {
        "model": model_name,
        "display_name": display_name,
        "field_count": len(field_info),
        "available_fields": list(field_info.keys()),
        "fields": {}
    }

    for fname, fmeta in field_info.items():
        meta["fields"][fname] = {
            "label": fmeta.get("string", ""),
            "type": fmeta.get("type", ""),
            "relation": fmeta.get("relation", ""),
            "required": fmeta.get("required", False),
            "readonly": fmeta.get("readonly", False)
        }

    return {"success": True, "meta": meta}


# ==============================================================================
# MUTATION / WRITE BUILT-IN TOOL IMPLEMENTATIONS
# ==============================================================================

@mcp_tool(
    name="odoo_create_record",
    description="Create a new record in any allowed Odoo model.",
    category="Generic Write",
    read_only=False,
    input_schema={
        "type": "object",
        "properties": {
            "model": {"type": "string", "description": "Target Odoo model name (e.g. crm.lead, res.partner)"},
            "values": {"type": "object", "description": "Field values key-value mapping to create the record"}
        },
        "required": ["model", "values"]
    }
)
def handle_create_record(env, params):
    model_name = params.get('model')
    values = params.get('values')

    if not model_name or model_name not in env:
        return {"success": False, "error": {"code": "unknown_model", "message": f"Model '{model_name}' does not exist."}}

    if not isinstance(values, dict) or not values:
        return {"success": False, "error": {"code": "missing_values", "message": "Field values object is required to create a record."}}

    # Validate model permission
    if not env['mcp.model.rule'].check_permission(model_name, 'create'):
        return {"success": False, "error": {"code": "access_denied", "message": f"Create permission is disabled for model '{model_name}'."}}

    try:
        import odoo
        m_env = odoo.api.Environment(env.cr, 2, dict(env.context, mail_create_nosubscribe=True, tracking_disable=True, active_test=False))
        try:
            from odoo.http import request
            if request:
                request._env = m_env
        except Exception:
            pass

        model_obj = m_env[model_name]
        fields_info = model_obj.fields_get()

        invalid_fields = [f for f in values.keys() if f not in fields_info]
        if invalid_fields:
            return {"success": False, "error": {"code": "invalid_fields", "message": f"Fields {invalid_fields} do not exist on model '{model_name}'."}}

        rec = model_obj.create(values)
        created_data = rec.read()[0]
        rec_id = rec.id
        rec_name = rec.display_name

        cleaned = {}
        for k, v in created_data.items():
            if isinstance(v, (bytes, bytearray)):
                cleaned[k] = "<binary_data>"
            else:
                cleaned[k] = v

        # Audit Log
        odoo.api.Environment(env.cr, odoo.SUPERUSER_ID, env.context)['mcp.audit.log'].create({
            'user_id': 2,
            'tool_name': 'odoo_create_record',
            'model_name': model_name,
            'action_type': 'record_created',
            'status': 'success',
            'record_id': rec_id,
            'request_payload': json.dumps({'model': model_name, 'values': values})
        })

        return {
            "success": True,
            "id": rec_id,
            "display_name": rec_name,
            "created_fields": list(values.keys()),
            "data": cleaned
        }
    except Exception as e:
        env.cr.rollback()
        _logger.error(f"Error in odoo_create_record for {model_name}: {e}", exc_info=True)
        try:
            env['mcp.audit.log'].sudo().create({
                'user_id': 2,
                'tool_name': 'odoo_create_record',
                'model_name': model_name,
                'action_type': 'record_created',
                'status': 'error',
                'error_message': str(e),
                'request_payload': json.dumps({'model': model_name, 'values': values})
            })
        except Exception:
            pass
        return {"success": False, "error": {"code": "orm_error", "message": str(e)}}


@mcp_tool(
    name="odoo_write_record",
    description="Update an existing record in any allowed Odoo model by ID.",
    category="Generic Write",
    read_only=False,
    input_schema={
        "type": "object",
        "properties": {
            "model": {"type": "string", "description": "Target Odoo model name (e.g. crm.lead, res.partner)"},
            "id": {"type": "integer", "description": "Target record ID to update"},
            "values": {"type": "object", "description": "Field values key-value mapping to update"}
        },
        "required": ["model", "id", "values"]
    }
)
def handle_write_record(env, params):
    model_name = params.get('model')
    rec_id = params.get('id')
    values = params.get('values')

    if not model_name or model_name not in env:
        return {"success": False, "error": {"code": "unknown_model", "message": f"Model '{model_name}' does not exist."}}

    if not rec_id:
        return {"success": False, "error": {"code": "missing_id", "message": "Record ID is required for write operation."}}

    if not isinstance(values, dict) or not values:
        return {"success": False, "error": {"code": "missing_values", "message": "Field values object is required to update a record."}}

    # Validate model permission
    if not env['mcp.model.rule'].check_permission(model_name, 'write'):
        return {"success": False, "error": {"code": "access_denied", "message": f"Update permission is disabled for model '{model_name}'."}}

    try:
        import odoo
        m_env = odoo.api.Environment(env.cr, 2, dict(env.context, mail_create_nosubscribe=True, tracking_disable=True, active_test=False))
        try:
            from odoo.http import request
            if request:
                request._env = m_env
        except Exception:
            pass

        model_obj = m_env[model_name]
        rec = model_obj.browse(rec_id)
        if not rec.exists():
            return {"success": False, "error": {"code": "record_not_found", "message": f"Record #{rec_id} not found on model '{model_name}'."}}

        fields_info = model_obj.fields_get()
        invalid_fields = [f for f in values.keys() if f not in fields_info]
        if invalid_fields:
            return {"success": False, "error": {"code": "invalid_fields", "message": f"Fields {invalid_fields} do not exist on model '{model_name}'."}}

        rec.write(values)
        disp_name = rec.display_name

        # Audit Log
        odoo.api.Environment(env.cr, odoo.SUPERUSER_ID, env.context)['mcp.audit.log'].create({
            'user_id': 2,
            'tool_name': 'odoo_write_record',
            'model_name': model_name,
            'action_type': 'record_updated',
            'status': 'success',
            'record_id': rec_id,
            'request_payload': json.dumps({'model': model_name, 'id': rec_id, 'values': values})
        })

        return {
            "success": True,
            "id": rec_id,
            "record_name": disp_name,
            "updated_fields": list(values.keys())
        }
    except Exception as e:
        env.cr.rollback()
        _logger.error(f"Error in odoo_write_record for {model_name} #{rec_id}: {e}", exc_info=True)
        try:
            env['mcp.audit.log'].sudo().create({
                'user_id': 2,
                'tool_name': 'odoo_write_record',
                'model_name': model_name,
                'action_type': 'record_updated',
                'status': 'error',
                'record_id': rec_id,
                'error_message': str(e),
                'request_payload': json.dumps({'model': model_name, 'id': rec_id, 'values': values})
            })
        except Exception:
            pass
        return {"success": False, "error": {"code": "orm_error", "message": str(e)}}


@mcp_tool(
    name="odoo_delete_record",
    description="Delete an existing record in any allowed Odoo model by ID.",
    category="Generic Write",
    read_only=False,
    input_schema={
        "type": "object",
        "properties": {
            "model": {"type": "string", "description": "Target Odoo model name (e.g. crm.lead, res.partner)"},
            "id": {"type": "integer", "description": "Target record ID to delete"}
        },
        "required": ["model", "id"]
    }
)
def handle_delete_record(env, params):
    model_name = params.get('model')
    rec_id = params.get('id')

    if not model_name or model_name not in env:
        return {"success": False, "error": {"code": "unknown_model", "message": f"Model '{model_name}' does not exist."}}

    if not rec_id:
        return {"success": False, "error": {"code": "missing_id", "message": "Record ID is required for delete operation."}}

    # Validate model permission
    if not env['mcp.model.rule'].check_permission(model_name, 'delete'):
        return {"success": False, "error": {"code": "access_denied", "message": f"Delete permission is disabled for model '{model_name}'."}}

    try:
        import odoo
        with env.registry.cursor() as cr:
            m_env = odoo.api.Environment(cr, 2, {'mail_create_nosubscribe': True, 'tracking_disable': True, 'active_test': False})
            try:
                from odoo.http import request
                if request:
                    request._env = m_env
            except Exception:
                pass
            model_obj = m_env[model_name]
            rec = model_obj.browse(rec_id)
            if not rec.exists():
                return {"success": False, "error": {"code": "record_not_found", "message": f"Record #{rec_id} not found on model '{model_name}'."}}

            disp_name = rec.display_name
            rec.unlink()

            # Audit Log
            odoo.api.Environment(env.cr, odoo.SUPERUSER_ID, env.context)['mcp.audit.log'].create({
                'user_id': 2,
                'tool_name': 'odoo_delete_record',
                'model_name': model_name,
                'action_type': 'record_deleted',
                'status': 'success',
                'record_id': rec_id,
                'request_payload': json.dumps({'model': model_name, 'id': rec_id})
            })

            return {
                "success": True,
                "deleted_id": rec_id,
                "message": f"Record #{rec_id} ({disp_name}) deleted successfully."
            }
    except Exception as e:
        _logger.error(f"Error in odoo_delete_record for {model_name} #{rec_id}: {e}", exc_info=True)
        try:
            env['mcp.audit.log'].sudo().create({
                'user_id': 2,
                'tool_name': 'odoo_delete_record',
                'model_name': model_name,
                'action_type': 'record_deleted',
                'status': 'error',
                'record_id': rec_id,
                'error_message': str(e),
                'request_payload': json.dumps({'model': model_name, 'id': rec_id})
            })
        except Exception:
            pass
        return {"success": False, "error": {"code": "orm_error", "message": str(e)}}
