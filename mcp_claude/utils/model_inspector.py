# -*- coding: utf-8 -*-
"""
ModelInspector Utility Class
Stateless model introspection engine for Odoo 18.
Detects model type, mixins, safe fields, and operations capabilities.
"""

import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger(__name__)

# System/sensitive field names to exclude automatically from generic read operations
SENSITIVE_FIELD_NAMES = {
    'password', 'secret', 'api_key', 'access_token', 'refresh_token',
    'client_secret', 'private_key', 'auth_token', 'app_secret'
}

class ModelInspector:

    @classmethod
    def detect_model_type(cls, model_obj: Any) -> str:
        """
        Detect Odoo Model Type.
        Returns:
            'abstract'   for models.AbstractModel
            'transient'  for models.TransientModel
            'persistent' for models.Model
        """
        if getattr(model_obj, '_abstract', False):
            return 'abstract'
        if getattr(model_obj, '_transient', False):
            return 'transient'
        return 'persistent'

    @classmethod
    def detect_mixins(cls, model_obj: Any) -> List[str]:
        """Detect mixin inheritance on the given Odoo model object."""
        inherits = getattr(model_obj, '_inherit', [])
        if isinstance(inherits, str):
            inherits = [inherits]
        inherits = inherits or []
        mixins = [i for i in inherits if i in (
            'mail.thread', 'mail.activity.mixin', 'portal.mixin',
            'website.mixin', 'image.mixin', 'rating.mixin'
        )]
        return mixins

    @classmethod
    def get_model_capabilities(cls, model_obj: Any) -> Dict[str, bool]:
        """
        Build capability matrix for the given Odoo model.
        Returns dictionary mapping operations to boolean support.
        """
        m_type = cls.detect_model_type(model_obj)
        
        if m_type == 'abstract':
            return {
                'search': False,
                'search_read': False,
                'read': False,
                'create': False,
                'write': False,
                'unlink': False,
                'aggregate': False,
                'explain': True,
                'call_method': True
            }
        elif m_type == 'transient':
            return {
                'search': True,
                'search_read': True,
                'read': True,
                'create': True,
                'write': True,
                'unlink': False, # Prevent accidental unlinking of transient wizard context
                'aggregate': False,
                'explain': True,
                'call_method': True
            }
        else: # persistent models.Model
            return {
                'search': True,
                'search_read': True,
                'read': True,
                'create': True,
                'write': True,
                'unlink': True,
                'aggregate': True,
                'explain': True,
                'call_method': True
            }

    @classmethod
    def get_safe_fields(cls, model_obj: Any, requested_fields: Optional[List[str]] = None) -> List[str]:
        """
        Automatically analyze model fields and return safe stored field names for search_read/read.
        Excludes:
          - Computed chatter fields (message_*, activity_*)
          - Binary/image payloads
          - Security sensitive fields (password, secret, etc.)
        """
        try:
            fields_meta = model_obj.fields_get()
        except Exception as e:
            _logger.warning("Error fetching fields_get for model %s: %s", model_obj._name, e)
            return ['id', 'display_name']

        safe_fields = []
        for fname, fmeta in fields_meta.items():
            # Filter requested fields if explicit list provided
            if requested_fields and fname not in requested_fields:
                continue

            # Exclude chatter and activity computed fields
            if fname.startswith('message_') or fname.startswith('activity_') or fname in ('has_message', 'my_activity_date_deadline'):
                continue

            # Exclude sensitive security fields
            if fname in SENSITIVE_FIELD_NAMES:
                continue

            # Exclude binary / heavy payloads
            ftype = fmeta.get('type', '')
            if ftype in ('binary', 'html', 'reference'):
                continue

            # Ensure field is stored or safe basic field
            is_stored = fmeta.get('store', True)
            if not is_stored and fname not in ('id', 'name', 'display_name'):
                continue

            safe_fields.append(fname)

        if 'id' not in safe_fields and 'id' in fields_meta:
            safe_fields.insert(0, 'id')
        if 'display_name' not in safe_fields and 'display_name' in fields_meta:
            safe_fields.append('display_name')

        return safe_fields
