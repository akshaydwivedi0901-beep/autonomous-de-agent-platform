from langgraph.graph import StateGraph, END

from app.state.agent_state import AgentState

from app.agents.ba_agent import ba_agent
from app.agents.router_agent import router_agent
from app.agents.rag_agent import rag_agent
from app.agents.sql_agent import sql_agent
from app.agents.validator_agent import validator_agent
from app.agents.explain_agent import explain_agent
from app.agents.executor_agent import executor_agent
from app.agents.reflection_agent import reflection_agent
from app.agents.audit_agent import audit_agent


MAX_RETRIES = 3


# -------------------------
# Router decision
# -------------------------

def route_after_router(state: AgentState):

    if state.route == "RAG":
        return "rag"

    if state.route == "SQL":
        return "sql"

    # default fallback
    return "sql"


# -------------------------
# Validation routing
# -------------------------

def route_after_validation(state: AgentState):

    if state.validation_status == "INVALID":

        if state.retry_count < MAX_RETRIES:
            state.retry_count += 1
            return "sql"

        return "audit"

    return "explain"


# -------------------------
# Explain routing
# -------------------------

def route_after_explain(state: AgentState):

    if state.status == "EXPLAIN_FAILED":

        if state.retry_count < MAX_RETRIES:
            state.retry_count += 1
            return "sql"

        return "audit"

    return "execute"


# -------------------------
# Reflection routing
# -------------------------

def route_after_reflection(state: AgentState):

    if state.status == "REFLECTION_RETRY":

        if state.retry_count < MAX_RETRIES:
            state.retry_count += 1
            return "sql"

        return "audit"

    return "audit"


# -------------------------
# Build Graph
# -------------------------

def build_graph():

    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("ba", ba_agent)
    graph.add_node("router", router_agent)
    graph.add_node("rag", rag_agent)

    graph.add_node("sql", sql_agent)
    graph.add_node("validate", validator_agent)
    graph.add_node("explain", explain_agent)
    graph.add_node("execute", executor_agent)
    graph.add_node("reflect", reflection_agent)

    graph.add_node("audit", audit_agent)

    # Entry
    graph.set_entry_point("ba")

    # Planner → Router
    graph.add_edge("ba", "router")

    # Router → Tool selection
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "rag": "rag",
            "sql": "sql"
        }
    )

    # RAG path
    graph.add_edge("rag", "audit")

    # SQL pipeline
    graph.add_edge("sql", "validate")

    graph.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "sql": "sql",
            "explain": "explain",
            "audit": "audit"
        }
    )

    graph.add_conditional_edges(
        "explain",
        route_after_explain,
        {
            "sql": "sql",
            "execute": "execute",
            "audit": "audit"
        }
    )

    graph.add_edge("execute", "reflect")

    graph.add_conditional_edges(
        "reflect",
        route_after_reflection,
        {
            "sql": "sql",
            "audit": "audit"
        }
    )

    graph.add_edge("audit", END)

    return graph.compile()