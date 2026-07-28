# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

class SSETransportHandler:
    def __init__(self):
        _logger.debug("Initializing SSETransportHandler")

    def establish_connection(self, client_id: str):
        _logger.info("Establishing SSE stream for client: %s", client_id)

    def send_event(self, client_id: str, event_type: str, data: str):
        _logger.info("Sending SSE event %s to client %s", event_type, client_id)
