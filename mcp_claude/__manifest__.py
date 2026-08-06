# -*- coding: utf-8 -*-
{
    'name': "Secure Claude Integration & MCP Server for Odoo",
    'summary': "Security-first Odoo Claude integration & MCP server with model allowlists, approval queue, field deny rules, audit logs and read-first ERP tools.",
    'description': """
Secure Claude Integration & MCP Server for Odoo
===============================================

Connect Claude safely to Odoo without giving AI unrestricted ERP access.
Security-first MCP server with model allowlist/denylist, field-level deny rules,
human approval queue for writes, full audit trail, OAuth PKCE, encrypted API keys
and a control center.
    """,
    'author': "Solutions Master",
    'website': "https://extension.mybroadcast.online",
    'support': "developer.lifetips@gmail.com",
    'live_test_url': "https://extension.mybroadcast.online",
    'price': 99.00,
    'currency': 'USD',

    'category': 'Productivity',
    'version': '18.0.1.0.3',
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
        'views/mcp_analytics_dashboard_views.xml',
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
