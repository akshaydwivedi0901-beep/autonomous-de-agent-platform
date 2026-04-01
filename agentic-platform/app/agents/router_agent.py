import logging
from app.state.agent_state import AgentState

logger = logging.getLogger(__name__)

# =========================================
# KEYWORD SCORING
# =========================================
SQL_KEYWORDS = [
    "revenue", "sales", "sum", "count", "average", "avg",
    "total", "how many", "last quarter", "this month", "this year",
    "top", "rank", "customer", "order", "orders", "product",
    "supplier", "price", "profit", "loss", "growth", "trend",
    "compare", "breakdown", "highest", "lowest", "between",
]

RAG_KEYWORDS = [
    "what is", "explain", "define", "describe", "how does",
    "tell me about", "meaning", "concept", "policy", "document",
    "what are", "why is", "overview", "summary", "background",
]


def _score(question: str, keywords: list) -> int:
    q = question.lower()
    return sum(1 for k in keywords if k in q)


# =========================================
# AGENT
# =========================================
def router_agent(state: AgentState) -> AgentState:

    try:
        logger.info("🔥 ROUTER START")

        question = state.question or ""

        sql_score = _score(question, SQL_KEYWORDS)
        rag_score = _score(question, RAG_KEYWORDS)

        logger.info(f"Scores → SQL: {sql_score}, RAG: {rag_score}")

        # =============================
        # ROUTING DECISION
        # =============================
        if sql_score > 0 and rag_score > 0:
            # Both signals present → HYBRID (RAG enriches SQL answer)
            state.route = "HYBRID"

        elif rag_score > sql_score:
            state.route = "RAG"

        else:
            # Default to SQL (handles pure data questions + ties)
            state.route = "SQL"

        logger.info(f"✅ Route decided: {state.route}")

        return state

    except Exception as e:
        logger.error(f"❌ ROUTER FAILED: {e}")
        state.route = "SQL"
        return state