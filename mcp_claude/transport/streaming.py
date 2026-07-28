# -*- coding: utf-8 -*-
import logging
from typing import Any

_logger = logging.getLogger(__name__)

class StreamingTransportHandler:
    def __init__(self):
        _logger.debug("Initializing StreamingTransportHandler (Extension Stub)")

    def stream_chunk(self, chunk_data: Any):
        pass
