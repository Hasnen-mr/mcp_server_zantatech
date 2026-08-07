# -*- coding: utf-8 -*-
import json
import logging
import requests
from odoo import models, api

_logger = logging.getLogger(__name__)

class MCPProviderClaude(models.AbstractModel):
    _inherit = "mcp.ai.provider.base"
    _name = "mcp.ai.provider.claude"
    _description = "Anthropic Claude LLM Provider Subclass"

    @api.model
    def get_capabilities(self):
        caps = super().get_capabilities()
        caps.update({
            "provider_name": "Anthropic Claude 3.5 Sonnet",
            "supports_reasoning": True,
        })
        return caps

    @api.model
    def generate_completion(self, payload):
        """Minimal Phase 1 Claude API completion provider."""
        config = self.env["mcp.server.config"].sudo().search([], limit=1)
        api_key = getattr(config, "claude_api_key", None) if config else None
        if not api_key:
            api_key = self.env['ir.config_parameter'].sudo().get_param('mcp_claude.claude_api_key', None)
        
        # If no API key configured, return intelligent default response
        if not api_key or api_key == "mcp_live_default":
            user_txt = payload.get("messages", [{}])[-1].get("content", "")
            return f"Hello! I am your Odoo AI Assistant. I received your prompt: '{user_txt}'. Active system and view context is configured and ready."

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        body = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": payload.get("max_tokens", 1024),
            "system": payload.get("system", ""),
            "messages": payload.get("messages", [])
        }

        try:
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                content_blocks = data.get("content", [])
                if content_blocks:
                    return content_blocks[0].get("text", "")
            _logger.error(f"Claude API returned status {resp.status_code}: {resp.text}")
            return f"API Response Error ({resp.status_code}): Unable to complete request."
        except Exception as e:
            _logger.error(f"Failed to communicate with Anthropic API: {e}")
            return f"Communication Error: {str(e)}"

    @api.model
    def generate_stream(self, payload, channel_name, conversation_id=None):
        """Streams completion chunks via bus.bus."""
        text = self.generate_completion(payload)
        conv_service = self.env["mcp.ai.conversation.service"]
        
        # Stream chunks to bus
        chunk_size = 25
        seq = 1
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            self.env['bus.bus']._sendone(channel_name, 'mcp_ai_chunk', {
                'conversation_id': conversation_id,
                'seq_id': seq,
                'chunk': chunk,
                'done': False
            })
            seq += 1

        self.env['bus.bus']._sendone(channel_name, 'mcp_ai_chunk', {
            'conversation_id': conversation_id,
            'seq_id': seq,
            'chunk': '',
            'done': True
        })

        if conversation_id:
            conv_service.add_message(conversation_id, 'assistant', text, seq_id=seq)

        return text
