# -*- coding: utf-8 -*-
{
    'name': 'MCP Claude',
    'version': '18.0.1.0.0',
    'category': 'Technical/API',
    'summary': 'Model Context Protocol (MCP) Server for Odoo with OAuth 2.0 PKCE & API Key Auth',
    'description': """
Enterprise-Grade Odoo 18 MCP Claude
=======================================
Allows AI Clients (Claude, Cursor, VS Code, ChatGPT, Gemini, Ollama, etc.)
to securely connect to Odoo using Model Context Protocol (MCP).
""",
    'author': 'Enterprise AI Architecture Team',
    'website': 'https://github.com/odoo-mcp/mcp_claude',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
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
    'assets': {
        'web.assets_backend': [
            'mcp_claude/static/src/scss/control_center.scss',
            'mcp_claude/static/src/js/control_center.js',
            'mcp_claude/static/src/xml/control_center.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
