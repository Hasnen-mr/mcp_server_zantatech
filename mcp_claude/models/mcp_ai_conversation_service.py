# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class MCPConversationService(models.AbstractModel):
    _name = "mcp.ai.conversation.service"
    _description = "Conversation Management & Hybrid Scope Orchestration Service"

    @api.model
    def create_session(self, user_id=None, device_info=None):
        """Creates a new user AI session record."""
        target_user = user_id or self.env.user.id
        session = self.env["mcp.ai.session"].sudo().create({
            "name": f"Session {fields.Date.today()}",
            "user_id": target_user,
            "company_id": self.env.company.id,
            "device_info": device_info or "WebClient Browser",
            "schema_version": 2,
        })
        return session.id

    @api.model
    def get_or_create_conversation(self, session_id=None, scope=None, model_name=None, res_id=None, workspace_app=None):
        """Finds active conversation matching the scope context hierarchy or initializes a new thread."""
        user = self.env.user
        domain = [("user_id", "=", user.id), ("active", "=", True)]
        if session_id:
            domain.append(("id", "=", session_id))
        
        session = self.env["mcp.ai.session"].sudo().search(domain, limit=1)
        if not session:
            session_id = self.create_session(user_id=user.id)
            session = self.env["mcp.ai.session"].sudo().browse(session_id)

        # Infer scope if not explicitly provided
        if not scope:
            if model_name and res_id:
                scope = "record"
            elif model_name:
                scope = "module"
            elif workspace_app:
                scope = "workspace"
            else:
                scope = "global"

        conv_domain = [("session_id", "=", session.id), ("scope", "=", scope)]

        if scope == "record" and model_name and res_id:
            conv_domain.extend([("current_model", "=", model_name), ("current_res_id", "=", res_id)])
        elif scope == "module" and model_name:
            conv_domain.append(("current_model", "=", model_name))
        elif scope == "workspace" and workspace_app:
            conv_domain.append(("workspace_app", "=", workspace_app))

        conversation = self.env["mcp.ai.conversation"].sudo().search(conv_domain, order="id desc", limit=1)
        
        if not conversation:
            # Build clean title based on scope
            if scope == "record" and model_name and res_id:
                title = f"{model_name} #{res_id}"
            elif scope == "module" and model_name:
                title = f"{model_name} Module Chat"
            elif scope == "workspace" and workspace_app:
                title = f"{workspace_app.capitalize()} Workspace"
            else:
                title = "Global AI Assistant"

            conversation = self.env["mcp.ai.conversation"].sudo().create({
                "name": title,
                "session_id": session.id,
                "user_id": user.id,
                "company_id": self.env.company.id,
                "scope": scope,
                "current_model": model_name or False,
                "current_res_id": res_id or False,
                "workspace_app": workspace_app or False,
                "state": "idle",
                "schema_version": 2,
            })

        return {
            "session_id": session.id,
            "conversation_id": conversation.id,
            "title": conversation.name,
            "scope": conversation.scope,
            "current_model": conversation.current_model,
            "current_res_id": conversation.current_res_id,
            "workspace_app": conversation.workspace_app,
            "state": conversation.state,
        }

    @api.model
    def add_message(self, conversation_id, role, content, context_snapshot=None, seq_id=0, block_type="markdown"):
        """Appends a new persistent message record to the conversation."""
        conv = self.env["mcp.ai.conversation"].sudo().browse(conversation_id)
        if not conv.exists():
            return False

        snapshot_str = json.dumps(context_snapshot) if isinstance(context_snapshot, dict) else context_snapshot
        msg = self.env["mcp.ai.message"].sudo().create({
            "conversation_id": conv.id,
            "role": role,
            "content": content,
            "seq_id": seq_id,
            "context_snapshot": snapshot_str or False,
            "block_type": block_type,
        })
        return {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "seq_id": msg.seq_id,
            "block_type": msg.block_type,
        }

    @api.model
    def get_history(self, conversation_id, limit=50):
        """Returns ordered message history formatted for LLM consumption."""
        conv = self.env["mcp.ai.conversation"].sudo().browse(conversation_id)
        if not conv.exists():
            return []

        messages = self.env["mcp.ai.message"].sudo().search(
            [("conversation_id", "=", conv.id)],
            order="sequence asc, id asc",
            limit=limit
        )
        return [{
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "block_type": m.block_type,
            "seq_id": m.seq_id,
        } for m in messages]
