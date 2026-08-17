# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

class SessionManagerService:
    def __init__(self, env):
        self.env = env

    def update_session(self, client_id: str, transport_type: str, client_name: str):
        pass
