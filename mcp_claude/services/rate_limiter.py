# -*- coding: utf-8 -*-
import time
import logging

_logger = logging.getLogger(__name__)

# Failed attempts in-memory store: { ip_address: [timestamp1, timestamp2, ...] }
FAILED_ATTEMPTS = {}
LOCKOUT_DURATION = 900 # 15 minutes lockout
MAX_FAILED_ATTEMPTS = 5

class RateLimiter:
    @classmethod
    def is_ip_locked(cls, ip_addr: str) -> bool:
        if ip_addr in ("127.0.0.1", "localhost", "::1"):
            return False
        now = time.time()
        attempts = FAILED_ATTEMPTS.get(ip_addr, [])
        # Filter attempts within lockout window
        recent = [t for t in attempts if now - t < LOCKOUT_DURATION]
        FAILED_ATTEMPTS[ip_addr] = recent
        return len(recent) >= MAX_FAILED_ATTEMPTS

    @classmethod
    def record_failed_attempt(cls, ip_addr: str):
        if ip_addr in ("127.0.0.1", "localhost", "::1"):
            return
        now = time.time()
        attempts = FAILED_ATTEMPTS.get(ip_addr, [])
        attempts.append(now)
        FAILED_ATTEMPTS[ip_addr] = attempts
        _logger.warning(f"Failed Auth attempt from IP {ip_addr}. Total recent failures: {len(attempts)}")

    @classmethod
    def reset_ip(cls, ip_addr: str):
        if ip_addr in FAILED_ATTEMPTS:
            del FAILED_ATTEMPTS[ip_addr]
