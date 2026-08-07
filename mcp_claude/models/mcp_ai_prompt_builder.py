# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

class MCPPromptBuilder(models.AbstractModel):
    _name = "mcp.ai.prompt.builder"
    _description = "System Prompt & Context Normalizer"

    @api.model
    def build_system_prompt(self, conversation, active_context=None):
        """Aggregates System Directives, Extracted Context, and Model Rules into system prompt string."""
        prompt_parts = [
            "You are the official AI Assistant inside Odoo 18.",
            "You help users manage ERP workflows, query records, execute tools safely, and analyze data.",
            f"User: {self.env.user.name} (ID: {self.env.user.id}) | Company: {self.env.company.name} (ID: {self.env.company.id})"
        ]

        if conversation and conversation.current_model:
            prompt_parts.append(f"Active Odoo Model: {conversation.current_model}")
            if conversation.current_res_id:
                prompt_parts.append(f"Active Record ID: {conversation.current_res_id}")

        if active_context and isinstance(active_context, dict):
            prompt_parts.append("\n=== ACTIVE VIEW & SCREEN CONTEXT ===")
            prompt_parts.append(json.dumps(active_context, indent=2))

        return "\n".join(prompt_parts)

    @api.model
    def build_payload(self, conversation, user_prompt, active_context=None):
        """Assembles full LLM input payload including system prompt, active tools, and message history."""
        system_prompt = self.build_system_prompt(conversation, active_context)
        conv_service = self.env["mcp.ai.conversation.service"]
        history = conv_service.get_history(conversation.id) if conversation else []

        messages = []
        for msg in history:
            if msg["role"] in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_prompt})

        return {
            "system": system_prompt,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.3,
        }
