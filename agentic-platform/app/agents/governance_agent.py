# app/agents/governance_agent.py

import logging
from app.core.policies import ENV_POLICIES, FORBIDDEN_KEYWORDS, RESTRICTED_COLUMNS

logger = logging.getLogger(__name__)


def governance_agent(state):

    sql = (state.generated_sql or "").upper()
    policy = ENV_POLICIES.get(state.environment, ENV_POLICIES["dev"])

    risk_score = 0

    # 🚫 Hard-block forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql:
            state.governance_status = "BLOCKED_FORBIDDEN_KEYWORD"
            state.status = "BLOCKED"

            logger.warning({
                "execution_id": state.execution_id,
                "agent": "governance",
                "reason": keyword,
                "decision": state.governance_status
            })

            return state

    # 🚫 Block DELETE if not allowed
    if "DELETE" in sql and not policy["allow_delete"]:
        state.governance_status = "BLOCKED_DELETE_NOT_ALLOWED"
        state.status = "BLOCKED"

        logger.warning({
            "execution_id": state.execution_id,
            "agent": "governance",
            "decision": state.governance_status
        })

        return state

    # 🔍 Risk scoring
    if "SELECT *" in sql:
        risk_score += 20

    if "JOIN" in sql:
        join_count = sql.count("JOIN")
        risk_score += join_count * 10

    if "WHERE" not in sql and "SELECT" in sql:
        risk_score += 30

    for col in RESTRICTED_COLUMNS:
        if col in sql:
            risk_score += 50

    state.risk_score = risk_score

    # 🚫 Block if risk exceeds environment threshold
    if risk_score > policy["max_risk_score"]:
        state.governance_status = "BLOCKED_HIGH_RISK"
        state.status = "BLOCKED"

        logger.warning({
            "execution_id": state.execution_id,
            "agent": "governance",
            "risk_score": risk_score,
            "decision": state.governance_status
        })

        return state

    # ✅ Approved
    state.governance_status = "APPROVED"
    state.status = "GOVERNANCE_APPROVED"

    logger.info({
        "execution_id": state.execution_id,
        "agent": "governance",
        "risk_score": risk_score,
        "decision": state.governance_status
    })

    return state
