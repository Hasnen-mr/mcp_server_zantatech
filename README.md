# MCP Claude Control Center for Odoo (`mcp_claude`)

[![Odoo Version](https://img.shields.io/badge/Odoo-17.0%20%7C%2018.0%20%7C%2019.0-714B67?style=flat&logo=odoo)](https://www.odoo.com)
[![Protocol](https://img.shields.io/badge/MCP-JSON--RPC%202.0%20%2F%20SSE-blue)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-LGPL--3.0-green.svg)](LICENSE)

An enterprise-grade **Model Context Protocol (MCP)** server integrated directly into Odoo as an addon module (`mcp_claude`). It connects **Anthropic Claude Desktop** safely to your Odoo instance via Direct HTTPS OAuth 2.1 or Local Stdio Bridge.

---

## 📖 Overview

The **MCP Claude Control Center** brings Claude AI into your Odoo ERP environment with enterprise security guardrails. Rather than granting unrestricted database access, this module allows administrators to specify exact model rules, field deny policies, human approval requirements for write actions, and full audit logs.

---

## 🌟 Features

- **Purpose-Built Claude Integration**: Seamless integration with Anthropic Claude Desktop on macOS & Windows.
- **Dual Connection Modes**:
  - **Direct HTTPS OAuth 2.1**: High-performance remote URL connection using OAuth 2.1 PKCE authorization.
  - **Local Stdio Bridge**: 100% offline local workstation integration via standard I/O bridge executable (`bin/mcp_bridge.py`).
- **MCP Claude Control Center Dashboard**:
  - **Single-Question Tool Creator**: Wizard interface to safely register custom Odoo ORM search/read/write tools for Claude.
  - **Categorized Field Allowlist**: Restrict what data fields Claude can see.
  - **Governance Accordion**: Enforce human approval requirements on sensitive write/create/delete actions.
- **Fail-Proof Audit Logging**: Comprehensive record of every tool request, user context, target model, payload, and execution status.
- **Security-First Architectural Design**: Operates under standard user Odoo record rules and ACL permissions (no blind `sudo`).

---

## 📦 Supported Odoo Applications & Built-In Tools Library

The `mcp_claude` module includes an extensive library of curated built-in tools for all standard Odoo applications.

### Application Compatibility Table

| Application | Target Models | Built-In Tools | Required Odoo Module |
| :--- | :--- | :--- | :--- |
| **Contacts** | `res.partner` | `odoo_search_partners`, `odoo_get_contact`, `odoo_create_contact`, `odoo_update_contact`, `odoo_delete_contact`, `odoo_search_companies` | Core (`base`) |
| **CRM** | `crm.lead` | `odoo_search_leads`, `odoo_search_opportunities`, `odoo_create_lead`, `odoo_update_opportunity`, `odoo_move_opportunity_stage` | `crm` |
| **Sales** | `sale.order` | `odoo_search_quotations`, `odoo_search_orders`, `odoo_create_quotation`, `odoo_confirm_quotation`, `odoo_update_sales_order`, `odoo_cancel_sales_order` | `sale` |
| **Purchase** | `purchase.order` | `odoo_search_rfqs`, `odoo_search_purchase_orders`, `odoo_create_rfq`, `odoo_confirm_purchase_order`, `odoo_search_vendors` | `purchase` |
| **Inventory** | `product.product`, `stock.picking`, `stock.quant`, `stock.warehouse` | `odoo_search_products`, `odoo_get_product`, `odoo_create_product`, `odoo_update_product`, `odoo_search_stock`, `odoo_search_warehouses`, `odoo_search_locations`, `odoo_search_transfers` | `stock` / `product` |
| **Accounting** | `account.move`, `account.payment`, `account.journal`, `account.tax` | `odoo_search_invoices`, `odoo_search_vendor_bills`, `odoo_search_payments`, `odoo_create_invoice`, `odoo_register_payment`, `odoo_search_journals`, `odoo_search_taxes` | `account` |
| **Projects** | `project.project`, `project.task` | `odoo_search_projects`, `odoo_search_tasks`, `odoo_create_task`, `odoo_update_task`, `odoo_complete_task` | `project` |
| **Helpdesk** | `helpdesk.ticket` | `odoo_search_tickets`, `odoo_create_ticket`, `odoo_update_ticket` | `helpdesk` |
| **Employees** | `hr.employee`, `hr.department`, `hr.leave`, `hr.attendance` | `odoo_search_employees`, `odoo_search_departments`, `odoo_search_leaves`, `odoo_search_attendance` | `hr` |
| **Calendar** | `calendar.event` | `odoo_search_events`, `odoo_create_event`, `odoo_update_event` | `calendar` |
| **Discuss** | `mail.message`, `discuss.channel` | `odoo_search_channels`, `odoo_search_messages` | `mail` |
| **Manufacturing** | `mrp.production`, `mrp.bom` | `odoo_search_manufacturing_orders`, `odoo_create_manufacturing_order`, `odoo_search_boms` | `mrp` |
| **Expenses** | `hr.expense` | `odoo_search_expenses`, `odoo_create_expense` | `hr_expense` |
| **Timesheets** | `account.analytic.line` | `odoo_search_timesheets`, `odoo_create_timesheet_entry` | `hr_timesheet` |
| **Generic CRUD** | Any Allowed Model | `odoo_read_record`, `odoo_create_record`, `odoo_write_record`, `odoo_delete_record`, `odoo_aggregate`, `odoo_explain_record` | Core (`base`) |

### Module Auto-Detection & Uninstalled Apps Behavior
- The server automatically inspects the Odoo environment (`self.env`) during initialization.
- If a module (e.g., `mrp` or `helpdesk`) is not installed on the target database, its tools return an AI-friendly notice (`"note": "Module not installed"`) without raising crashes or ORM tracebacks.
- When an application is installed later, its corresponding built-in tools become available immediately upon server refresh.

---

## 🔍 Evidence-Based Compatibility Matrix

This compatibility classification distinguishes **personally tested behavior**, **officially documented behavior**, and **known platform constraints**:

| Platform / Installation | Connection Type | State | Evidence / Status |
| :--- | :--- | :---: | :--- |
| **Windows (Standard Installer)** | HTTPS / Stdio Bridge | `✅ Verified` | Tested on Windows 10/11 x64 workstation. Local stdio bridge verified. |
| **Windows (MS Store MSIX Package)** | HTTPS / Stdio Bridge | `🟡 Documented` | Officially documented AppContainer sandboxed path (`Packages\Claude_...`). |
| **macOS (App Bundle)** | HTTPS / Stdio Bridge | `🟡 Documented` | Officially documented path by Anthropic (`~/Library/Application Support/Claude`). |
| **Claude Web (`claude.ai`)** | Direct HTTPS OAuth | `🟡 Documented` | Web browsers cannot launch local stdio subprocesses due to W3C sandbox rules. Connect via Remote HTTPS URL. |
| **Linux Native Desktop** | Remote HTTPS URL | `🔴 Unsupported` | Anthropic does not produce a native Linux desktop app. Use Remote HTTPS OAuth or Wine environment. |

### Known Platform Constraints
1. **Claude Desktop Host Validation**:
   Claude Desktop enforces RFC 6761 loopback standards and rejects raw `localhost` or `127.0.0.1` strings for HTTPS connectors. Use **`odoo.localhost`** which automatically maps to `127.0.0.1` without modifying system `hosts` files.
2. **Microsoft Store MSIX Sandboxing**:
   The Microsoft Store packaging model isolates roaming AppData. Users must edit `claude_desktop_config.json` inside `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\`.

---

## 📋 Requirements

- **Odoo Version**: Odoo 17.0 / 18.0 / 19.0 (Community or Enterprise edition)
- **Python Version**: Python 3.10+
- **Python Packages**: `pyjwt`, `cryptography`, `jsonschema`, `requests`
- **Claude Application**: [Anthropic Claude Desktop App](https://claude.ai/download) (macOS or Windows)

---

## 🚀 Installation

1. **Clone the Repository into your Odoo Addons Path**:
   ```bash
   git clone https://github.com/Hasnen-mr/mcp_server_zantatech.git mcp_claude
   ```

2. **Install Required Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the Module in Odoo**:
   - Activate **Developer Mode** in Odoo Settings.
   - Go to **Apps** ➔ Click **Update Apps List**.
   - Search for **Claude MCP Integration** (`mcp_claude`) and click **Activate**.

4. **Access the MCP Control Center**:
   - Navigate to **MCP ➔ Configurations** in the top navigation bar.

---

## 🔌 Connecting Claude

### Option A: Direct HTTPS URL Connection (Production Recommended)

1. Open **Claude Desktop App** ➔ Click your profile icon ➔ Select **Settings** ➔ **Connectors**.
2. Click **Add Custom Connector**.
3. Set **Name**: `Odoo Claude`
4. Set **URL**:
   ```text
   https://your-odoo-domain.com/mcp
   ```
5. Click **Add** and authenticate via Odoo OAuth.

### Option B: Local Stdio Bridge (Local Development / Offline)

Add the following snippet to your `claude_desktop_config.json`:

#### Windows Configuration Path:
`%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "odoo-claude": {
      "command": "D:\\Odoo\\venv\\Scripts\\python.exe",
      "args": [
        "D:\\odoo-mcp\\mcp_claude\\bin\\mcp_bridge.py"
      ],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "odoo18",
        "ODOO_TOKEN": "mcp_live_default"
      }
    }
  }
}
```

---

## 🔐 Authentication

- **OAuth 2.1 Dynamic Client Registration**: Automatic client registration compliant with RFC 7591 / RFC 8414.
- **Bearer API Keys**: Per-company encrypted API keys (`mcp.api.key`) for token-based authorization.

---

## 💻 Local Development

When testing locally over HTTPS without a public domain, use **`odoo.localhost`**:
1. Generate trusted local TLS certificates using `mkcert`:
   ```bash
   mkcert -cert-file certs/odoo_localhost.crt -key-file certs/odoo_localhost.key odoo.localhost *.localhost localhost 127.0.0.1 ::1
   ```
2. Point Claude Desktop Custom Connector URL to `https://odoo.localhost:8443/mcp`.

---

## 🌐 Production Deployment

- Ensure your Odoo instance is deployed behind Nginx or Apache with a valid SSL/TLS certificate.
- Ensure reverse proxy headers `X-Forwarded-Proto` and `X-Forwarded-Host` are passed to Werkzeug.

---

## 🛠️ Troubleshooting & FAQ

### 1. Claude Desktop shows "Host Not Allowed" on localhost
Use `odoo.localhost` instead of `localhost` or `127.0.0.1`. Claude Desktop host validation enforces RFC 6761 loopback domain standards.

### 2. Tools fail execution with Permission Error
Verify that the logged-in Odoo user has active ACL access to the requested Odoo model under **MCP ➔ Permissions**.

---

## 📄 License

This module is licensed under the **LGPL-3.0 License**.
