# -*- coding: utf-8 -*-
import secrets
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

SERVER_HMAC_SECRET = b"odoo_mcp_server_hmac_secret_key_v18"

class MCPApiKey(models.Model):
    _name = "mcp.api.key"
    _description = "MCP Security API Key & Opaque Token"

    name = fields.Char("Token Name", required=True, default="Claude Desktop")
    key_prefix = fields.Char("Key Prefix (Short ID)", index=True)
    key_hash = fields.Char("HMAC-SHA256 Hash", required=True, index=True)
    user_id = fields.Many2one("res.users", "Owner", required=True, default=lambda self: self.env.user)
    active = fields.Boolean("Active", default=True)
    scopes = fields.Selection([
        ('full', 'Full Access (Read/Write)'),
        ('read_only', 'Read Only'),
        ('tools_only', 'Tools Only Execution')
    ], string="Permission Scope", default='full')
    allowed_ips = fields.Char("Allowed IPs (Comma separated)", help="Optional IP whitelist")
    expiration_policy = fields.Selection([
        ('never', 'Never Expire'),
        ('30_days', '30 Days'),
        ('90_days', '90 Days'),
        ('custom', 'Custom Date')
    ], string="Expiration Policy", default='never')
    expires_at = fields.Datetime("Expires At")
    last_used_at = fields.Datetime("Last Used At")
    last_used_ip = fields.Char("Last Used IP")

    @api.model
    def hash_token(self, token_str: str) -> str:
        """Computes HMAC-SHA256 hash of token using server secret."""
        return hmac.new(SERVER_HMAC_SECRET, token_str.encode('utf-8'), hashlib.sha256).hexdigest()

    @api.model
    def generate_opaque_connector_token(self, name="Claude Desktop", scopes="full", expiration_policy="never", allowed_ips=None):
        """
        Generates high-entropy opaque random token (secrets.token_urlsafe(32)).
        Zero user info or prefix encoded into the raw token string.
        Persists only HMAC-SHA256 hash in DB. Returns raw token string ONCE to caller.
        """
        raw_token = secrets.token_urlsafe(32) # Pure opaque random string
        prefix = raw_token[:8]
        token_hash = self.hash_token(raw_token)

        expires_dt = None
        if expiration_policy == '30_days':
            expires_dt = datetime.now() + timedelta(days=30)
        elif expiration_policy == '90_days':
            expires_dt = datetime.now() + timedelta(days=90)

        record = self.create({
            "name": name,
            "key_prefix": prefix,
            "key_hash": token_hash,
            "user_id": self.env.user.id,
            "active": True,
            "scopes": scopes,
            "allowed_ips": allowed_ips,
            "expiration_policy": expiration_policy,
            "expires_at": expires_dt,
        })
        
        # Log Audit Trail
        self.env['mcp.audit.log'].sudo().create({
            "name": f"Generated Token: {name}",
            "res_model": "mcp.api.key",
            "res_id": record.id,
            "action_type": "create",
            "user_id": self.env.user.id
        })

        return raw_token, record

    def action_revoke(self):
        """Revokes token and immediately terminates all linked active sessions."""
        for rec in self:
            rec.active = False
            # Terminate active sessions
            sessions = self.env['mcp.session'].search([('user_id', '=', rec.user_id.id), ('state', '=', 'active')])
            sessions.write({'state': 'revoked'})
            
            # Audit Log
            self.env['mcp.audit.log'].sudo().create({
                "name": f"Revoked Token: {rec.name}",
                "res_model": "mcp.api.key",
                "res_id": rec.id,
                "action_type": "delete",
                "user_id": self.env.user.id
            })

    @api.model
    def action_revoke_all_user_tokens(self, user_id=None):
        """Emergency admin action to revoke all tokens for a user."""
        target_uid = user_id or self.env.user.id
        keys = self.search([('user_id', '=', target_uid), ('active', '=', True)])
        keys.action_revoke()
        return True
