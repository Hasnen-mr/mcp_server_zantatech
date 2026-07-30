# Odoo Model Context Protocol (MCP) Server (`mcp_claude`)

[![Odoo Version](https://img.shields.io/badge/Odoo-17.0%20%7C%2018.0%20%7C%2019.0-714B67?style=flat&logo=odoo)](https://www.odoo.com)
[![Protocol](https://img.shields.io/badge/MCP-JSON--RPC%202.0%20%2F%20SSE-blue)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-LGPL--3.0-green.svg)](LICENSE)

An enterprise-grade **Model Context Protocol (MCP)** server integrated directly into Odoo as an addon module (`mcp_claude`). It connects AI clients—such as **Claude Desktop**, **Cursor**, **ChatGPT**, and **VS Code**—to your Odoo instance safely via stdio or Remote SSE transport.

---

## 🌟 Key Features

- **Full MCP Transport Support**: Supports both **Local Stdio Bridge** (`sys.stdin`/`sys.stdout`) and **Remote Server-Sent Events (SSE)**.
- **Fail-Proof Audit Logging**: Real-time logging of tool invocations (`tools/call`) to the PostgreSQL `mcp_audit_log` table with user context, timestamps, model targets, and status.
- **Odoo Control Center & Configurations UI**:
  - In-app **Configurations** dashboard inside Odoo.
  - **Option 1 (Remote SSE URL)** and **Option 2 (Local Stdio JSON Code)** quick-copy cards.
  - **Permissions Sub-Tab**: Granular CRUD control toggles (Read, Create, Write, Delete) per Odoo app (Sales, Invoicing, Inventory, CRM, Contacts, HR, Purchase, Projects).
- **JSON-RPC 2.0 Compliance**: Clean Zod-compatible notification handling (HTTP 204 for notifications).

---

## 🔌 Connection Options

### Option 1: Remote SSE Transport (HTTPS)

Used for remote integrations or Claude Desktop Custom Connectors.

#### Setup for Local Offline Development (`mkcert`):
> **Important Note on Claude Desktop Host Validation**:  
> Claude Desktop client-side validation blocks literal loopback strings (`localhost`, `127.0.0.1`).  
> Use **`odoo.localhost`** which automatically resolves to `127.0.0.1` / `::1` (RFC 6761) without modifying your system `hosts` file.

1. **Generate Trusted Certificate with `mkcert`**:
   ```cmd
   mkcert -cert-file certs/odoo_localhost.crt -key-file certs/odoo_localhost.key odoo.localhost *.localhost localhost 127.0.0.1 ::1
   ```

2. **Add Custom Connector in Claude Desktop**:
   - **Name**: `Odoo Remote`
   - **URL**:
     ```text
     https://odoo.localhost:8443/mcp/v1/sse?token=mcp_live_default
     ```

---

### Option 2: Local Stdio Bridge (100% Offline)

Recommended for single-workstation local development without requiring network servers or TLS certificates.

Add the following configuration to your `claude_desktop_config.json`:

#### Windows Configuration Path:
`%APPDATA%\Claude\claude_desktop_config.json`  
*(If using Microsoft Store Claude Desktop, update inside `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`)*

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

## 🚀 Installation & Setup

1. **Clone the Repository into your Odoo Addons Path**:
   ```bash
   git clone https://github.com/Hasnen-mr/mcp_server_zantatech.git mcp_claude
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the Module in Odoo**:
   - Update Apps list in Odoo Developer Mode.
   - Install **Claude MCP Integration** (`mcp_claude`).

4. **Access Configurations UI**:
   - Navigate to **MCP ➔ Configurations** in the Odoo top menu.
   - Configure active integration tokens and manage app CRUD permissions.

---

## 🛠️ Repository Layout

- `mcp_claude/` — Core Odoo addon module (controllers, models, security, UI views).
  - `controllers/mcp.py` — JSON-RPC 2.0 & SSE HTTP endpoints.
  - `bin/mcp_bridge.py` — Stdio-to-HTTP bridge executable.
  - `static/src/` — Owl JS & QWeb control center templates.
- `certs/` — Storage for SSL certificates (ignored in git).
- `odoo.conf` — Odoo server configuration file.
- `requirements.txt` — Python package requirements (`pyjwt`, `cryptography`, `jsonschema`, `requests`).

---

## 📄 License

This module is licensed under the **LGPL-3.0 License**.
