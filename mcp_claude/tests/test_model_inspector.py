# -*- coding: utf-8 -*-
"""
Unit Test Suite for ModelInspector Utility (Phase 1-5 Capability Matrix Verification)
"""

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from unittest.mock import MagicMock
from utils.model_inspector import ModelInspector

class TestModelInspector(unittest.TestCase):

    def test_detect_model_type_persistent(self):
        model = MagicMock()
        model._abstract = False
        model._transient = False
        self.assertEqual(ModelInspector.detect_model_type(model), 'persistent')

    def test_detect_model_type_abstract(self):
        model = MagicMock()
        model._abstract = True
        model._transient = False
        self.assertEqual(ModelInspector.detect_model_type(model), 'abstract')

    def test_detect_model_type_transient(self):
        model = MagicMock()
        model._abstract = False
        model._transient = True
        self.assertEqual(ModelInspector.detect_model_type(model), 'transient')

    def test_detect_mixins(self):
        model = MagicMock()
        model._inherit = ['mail.thread', 'mail.activity.mixin', 'custom.mixin']
        mixins = ModelInspector.detect_mixins(model)
        self.assertIn('mail.thread', mixins)
        self.assertIn('mail.activity.mixin', mixins)
        self.assertNotIn('custom.mixin', mixins)

    def test_abstract_model_capabilities(self):
        model = MagicMock()
        model._abstract = True
        caps = ModelInspector.get_model_capabilities(model)
        self.assertFalse(caps['search'])
        self.assertFalse(caps['read'])
        self.assertFalse(caps['create'])
        self.assertFalse(caps['write'])
        self.assertFalse(caps['unlink'])
        self.assertTrue(caps['explain'])

    def test_persistent_model_capabilities(self):
        model = MagicMock()
        model._abstract = False
        model._transient = False
        caps = ModelInspector.get_model_capabilities(model)
        self.assertTrue(caps['search'])
        self.assertTrue(caps['read'])
        self.assertTrue(caps['create'])
        self.assertTrue(caps['write'])
        self.assertTrue(caps['unlink'])

    def test_get_safe_fields_filters_chatter_and_sensitive(self):
        model = MagicMock()
        model._name = 'test.model'
        model.fields_get.return_value = {
            'id': {'type': 'integer', 'store': True},
            'name': {'type': 'char', 'store': True},
            'password': {'type': 'char', 'store': True},
            'secret': {'type': 'char', 'store': True},
            'message_has_error': {'type': 'boolean', 'store': False},
            'activity_ids': {'type': 'one2many', 'store': False},
            'avatar': {'type': 'binary', 'store': True},
        }
        safe_fields = ModelInspector.get_safe_fields(model)
        self.assertIn('id', safe_fields)
        self.assertIn('name', safe_fields)
        self.assertNotIn('password', safe_fields)
        self.assertNotIn('secret', safe_fields)
        self.assertNotIn('message_has_error', safe_fields)
        self.assertNotIn('activity_ids', safe_fields)
        self.assertNotIn('avatar', safe_fields)

if __name__ == '__main__':
    unittest.main()
