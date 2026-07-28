# -*- coding: utf-8 -*-
{
    'name': "Odoo MCP Server | Model Context Protocol AI Connector | Claude Cursor ChatGPT Integration",

    'summary': "Secure Odoo MCP server for Claude, Cursor, ChatGPT, VS Code & Gemini — OAuth 2.0 PKCE, API keys, model permissions, AI tools, audit logs and control center.",

    'description': """
Odoo MCP Server — Model Context Protocol AI Connector for Claude, Cursor & ChatGPT
==================================================================================

SEO title: Odoo MCP Server | Model Context Protocol | AI Connector | Claude | Cursor | ChatGPT | OAuth API

Short description:
Best Model Context Protocol (MCP) server for Odoo. Connect Claude Desktop, Cursor, ChatGPT,
VS Code Copilot, Gemini and other AI clients to your Odoo data with enterprise security —
OAuth 2.0 PKCE, API keys, model permission rules, tool registry, approval workflow, sessions,
audit logs and an in-Odoo AI control center.

Full description:
Turn Odoo into an AI-ready backend using the open Model Context Protocol standard.
Give AI assistants controlled read/write access to selected Odoo models without exposing
your full database. Ideal for AI-assisted CRM, inventory lookups, support automation and
developer copilots that need live ERP context.

Top AI / MCP keywords
---------------------
Model Context Protocol, MCP server, Claude MCP, Cursor MCP, ChatGPT MCP, VS Code MCP,
Odoo AI integration, AI ERP connector, LLM tools, OAuth PKCE, API key auth,
AI agent Odoo, Anthropic Claude Desktop, OpenAI tools, Gemini tools

Key Features
------------
* Native Model Context Protocol (MCP) server for Odoo
* Connect Claude, Cursor, ChatGPT, VS Code, Gemini, Ollama and more
* OAuth 2.0 with PKCE for secure client authorization
* API key / opaque token authentication
* Model permission rules (allow / deny by model & operation)
* Registered MCP tools with schema-aware invocation
* Human-in-the-loop tool approval requests
* Live MCP client sessions monitoring
* Full audit log of tool calls and model access
* Metrics & dashboard control center inside Odoo
* Server configuration for endpoints and security policies

Who is this for
---------------
* Odoo partners building AI copilots for customers
* IT teams connecting Claude / Cursor to production Odoo
* SaaS operators who need audited AI access to ERP data
* Developers shipping MCP tools on top of Odoo models

Industries
----------
* Professional Services
* Distribution & Logistics
* Manufacturing
* Retail & eCommerce
* Healthcare admin
* Education
* Financial Services

Pricing
-------
* One-time Odoo Apps Store license (USD)
* Your own Odoo instance and AI client accounts

Requirements
------------
* Odoo 17 / 18 / 19 (matching branch)
* Python packages: pyjwt, cryptography, jsonschema, requests
* Public HTTPS URL recommended for remote AI clients (production)

Support
-------
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

    'category': 'Technical/API',
    'version': '18.0.1.0.1',
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
        'static/description/screenshot_security.png',
        'static/description/screenshot_tools.png',
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
