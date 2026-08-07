# -*- coding: utf-8 -*-
"""
Odoo Module Lifecycle Hooks for mcp_claude
Handles post-installation secret generation and migration updates.
"""

import logging
from .utils.crypto import generate_random_secret

_logger = logging.getLogger(__name__)

def post_init_hook(env):
    """
    Executed automatically after module installation.
    Generates a cryptographically secure 256-bit random HMAC secret
    in ir.config_parameter if missing.
    """
    try:
        config_param = env['ir.config_parameter'].sudo()
        existing_secret = config_param.get_param('mcp_claude.hmac_secret')
        if not existing_secret:
            new_secret = generate_random_secret(32)
            config_param.set_param('mcp_claude.hmac_secret', new_secret)
            _logger.info("Successfully generated and saved installation HMAC secret for mcp_claude.")
        else:
            _logger.info("mcp_claude.hmac_secret already exists in ir.config_parameter.")
    except Exception as e:
        _logger.warning(f"Warning in post_init_hook during HMAC secret setup: {e}")
