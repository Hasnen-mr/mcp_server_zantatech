# -*- coding: utf-8 -*-
{
    'name': "Secure AI Agent & MCP Server for Odoo | Claude, ChatGPT, Gemini with Approvals",

    'summary': "Security-first Odoo AI agent & MCP server — Claude, ChatGPT, Gemini, Cursor & Ollama with model allowlists, approval queue, field deny rules, audit logs and read-first ERP tools.",

    'description': """
Secure AI Agent & MCP Server for Odoo — Claude, ChatGPT, Gemini with Guardrails
===============================================================================

SEO title: Secure AI Agent & MCP Server for Odoo | Claude | ChatGPT | Gemini | MCP | AI Approvals | Audit Log

Short description:
Connect Claude Desktop, ChatGPT, Gemini, Cursor and Ollama to Odoo without giving AI unrestricted
ERP access. Security-first MCP server with model allowlist/denylist, field-level deny rules,
human approval queue for writes, full audit trail, OAuth PKCE, encrypted API keys and a control
center — read-first AI tools for partners, leads, orders and products.

Full description:
Buyers want AI in Odoo — but not "connect and hope." This module is your security-first AI agent
and Model Context Protocol (MCP) server: one installable product that beats free MCP servers with
approvals, field deny lists, user ACL respect (no blind sudo), and compliance-ready audit logs.

Suggested Apps Store positioning: App #4 Secure AI Agent for Odoo (MCP-lite)
Technical module name: mcp_claude

Top AI / MCP / agent keywords
-----------------------------
Secure AI agent Odoo, MCP server, AI bridge Odoo, Claude Odoo, ChatGPT Odoo, Gemini Odoo,
Cursor MCP, Ollama Odoo, AI approval workflow, AI guardrails, ERP AI connector,
Model Context Protocol, AI audit log, human in the loop AI, AI with permissions,
Odoo AI assistant, AI read-only tools, AI write approval, SOC2 AI audit, GDPR AI logging

MVP features (v1.0)
-------------------
Connections
* Connect Claude / ChatGPT / Gemini / local Ollama
* MCP server endpoint for Cursor / Claude Desktop
* Per-company API keys (encrypted storage)
* Connection health check and usage counter

Safe tools (read-first)
* Search partners, leads, orders, invoices, products (domain-limited)
* Read record by ID with field allowlist
* Aggregate reports on allowed models
* Explain record in plain language (summarize SO, invoice, lead)

Security core (your moat)
* Model allowlist / denylist
* Field-level deny (salary, bank, password, API keys)
* Record rules respected — user ACL, not sudo
* Write actions require human approval queue
* Approval UI: Accept / Reject / Edit payload
* Full audit log (prompt, tool calls, user, result)

UX in Odoo
* MCP control center dashboard
* Sessions, tools and metrics monitoring
* OAuth 2.0 PKCE and API key management
* Server configuration and security policies

Why teams choose this over free MCP
------------------------------------
* Free MCP servers often grant broad database access — you get approvals + field deny
* Claude connectors are "connect and hope" — you get audit + governance
* Full AI agent suites are complex and expensive — SMB-simple, security-first
* AI Bridge module suites need many installs — one product, one security model

Industries
----------
* Professional Services & Consulting
* Distribution & Logistics
* Manufacturing & Operations
* Retail & eCommerce
* Healthcare Administration
* Financial Services

Pricing
-------
* One-time Odoo Apps Store license: USD 99
* Your own Odoo instance and AI client accounts (Claude, OpenAI, Google, etc.)

Requirements
------------
* Odoo 17 / 18 / 19 (matching GitHub branch)
* Depends: base, web
* Python: pyjwt, cryptography, jsonschema, requests
* Public HTTPS URL recommended for remote AI clients (production)
* Optional integrations: crm, sale, account, documents (for extended read tools)

Support
-------
Author: Solutions Master
Professional implementation and customization available.
Email: developer.lifetips@gmail.com
Website: https://extension.mybroadcast.online
    """,

    'author': "Solutions Master",
    'website': "https://extension.mybroadcast.online",
    'support': "developer.lifetips@gmail.com",
    'live_test_url': "https://extension.mybroadcast.online",
    'price': 99.00,
    'currency': 'USD',

    'category': 'Productivity',
    'version': '17.0.1.0.2',
    'license': 'LGPL-3',

    'depends': ['base', 'web'],

    'external_dependencies': {
        'python': [
            'jwt',
            'cryptography',
            'jsonschema',
            'requests',
        ],
    },

    'data': [
        'security/mcp_security.xml',
        'security/ir.model.access.csv',
        'data/default_config.xml',
        'views/mcp_server_config_views.xml',
        'views/mcp_api_key_views.xml',
        'views/mcp_oauth_client_views.xml',
        'views/mcp_session_views.xml',
        'views/mcp_model_rule_views.xml',
        'views/mcp_tool_views.xml',
        'views/mcp_approval_request_views.xml',
        'views/mcp_audit_log_views.xml',
        'views/mcp_dashboard_views.xml',
        'views/menus.xml',
    ],

    'images': [
        'static/description/screenshot_dashboard.png',
        'static/description/screenshot_approvals.png',
        'static/description/screenshot_security.png',
        'static/description/product_overview.png',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,

    'assets': {
        'web.assets_backend': [
            'mcp_claude/static/src/scss/control_center.scss',
            'mcp_claude/static/src/js/control_center.js',
            'mcp_claude/static/src/xml/control_center.xml',
        ],
    },
}
