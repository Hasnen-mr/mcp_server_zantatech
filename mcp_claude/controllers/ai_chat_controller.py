# -*- coding: utf-8 -*-
import json
import logging
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)

class MCPAIChatController(http.Controller):

    @http.route('/mcp/ai/v1/chat/init', type='json', auth='user', methods=['POST'], csrf=False)
    def chat_init(self, session_id=None, scope=None, model_name=None, res_id=None, workspace_app=None, **kw):
        """Initializes or retrieves active conversation thread matching scope."""
        service = request.env['mcp.ai.conversation.service']
        res = service.get_or_create_conversation(
            session_id=session_id,
            scope=scope,
            model_name=model_name,
            res_id=res_id,
            workspace_app=workspace_app
        )
        history = service.get_history(res['conversation_id'])
        capabilities = request.env['mcp.ai.provider.claude'].get_capabilities()
        return {
            'success': True,
            'session_id': res['session_id'],
            'conversation_id': res['conversation_id'],
            'title': res['title'],
            'scope': res['scope'],
            'history': history,
            'capabilities': capabilities,
        }

    @http.route('/mcp/ai/v1/chat/message', type='json', auth='user', methods=['POST'], csrf=False)
    def chat_message(self, conversation_id, prompt, context_snapshot=None, **kw):
        """Processes user prompt and streams LLM response."""
        service = request.env['mcp.ai.conversation.service']
        prompt_builder = request.env['mcp.ai.prompt.builder']
        claude_provider = request.env['mcp.ai.provider.claude']
        pipeline = request.env['mcp.ai.response.pipeline']

        conv = request.env['mcp.ai.conversation'].sudo().browse(conversation_id)
        if not conv.exists():
            return {'success': False, 'error': 'Conversation thread not found'}

        # 1. Persist User Message
        user_msg = service.add_message(conv.id, 'user', prompt, context_snapshot=context_snapshot)

        # 2. Build Payload
        payload = prompt_builder.build_payload(conv, prompt, active_context=context_snapshot)

        # 3. Generate Stream via Bus Channel
        channel_name = f"mcp_ai_user_{request.env.user.id}_{conv.id}"
        conv.write({'state': 'streaming'})
        
        try:
            raw_response = claude_provider.generate_stream(payload, channel_name, conversation_id=conv.id)
            conv.write({'state': 'completed'})
            norm_block = pipeline.normalize_response(raw_response)
            return {
                'success': True,
                'user_message': user_msg,
                'response_block': norm_block,
                'channel_name': channel_name,
            }
        except Exception as e:
            conv.write({'state': 'failed'})
            _logger.error(f"Error in chat_message streaming: {e}")
            return {'success': False, 'error': str(e)}

    @http.route('/mcp/ai/v1/chat/history', type='json', auth='user', methods=['POST'], csrf=False)
    def chat_history(self, conversation_id, limit=50, **kw):
        """Retrieves history for conversation."""
        service = request.env['mcp.ai.conversation.service']
        history = service.get_history(conversation_id, limit=limit)
        return {'success': True, 'history': history}
