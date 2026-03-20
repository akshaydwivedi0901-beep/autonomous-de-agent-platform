"""Governance policy configuration for different environments.

This module centralizes simple governance settings and lists used by
policy checks across the platform.
"""
ENV_POLICIES = {
    "dev": {
        "allow_delete": True,
        "allow_drop": False,
        "max_risk_score": 80,
    },
    "test": {
        "allow_delete": False,
        "allow_drop": False,
        "max_risk_score": 60,
    },
    "prod": {
        "allow_delete": False,
        "allow_drop": False,
        "max_risk_score": 40,
    },
}

FORBIDDEN_KEYWORDS = ["DROP", "TRUNCATE"]

RESTRICTED_COLUMNS = ["SSN", "CREDIT_CARD", "PASSWORD"]
