# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

class MetricsService:
    def __init__(self, env):
        self.env = env

    def increment_counter(self, metric_name: str, count: int = 1):
        pass
