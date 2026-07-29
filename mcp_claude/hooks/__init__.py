# -*- coding: utf-8 -*-
import os
import sys
import logging
from odoo.addons.mcp_claude.bin.mcp_https_proxy import start_proxy_thread

_logger = logging.getLogger(__name__)

def post_load():
    try:
        active_port = start_proxy_thread()
        if active_port:
            _logger.info(f"MCP Trusted HTTPS Proxy Started Automatically on Port {active_port}")
        else:
            _logger.info("MCP HTTPS Proxy Pending: Run setup_localhost_ssl.py to activate SSL")
    except Exception as e:
        _logger.warning(f"Could not auto-start HTTPS Proxy: {e}")
