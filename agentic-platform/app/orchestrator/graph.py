import logging
from langgraph.graph import StateGraph, END

from app.state.agent_state import AgentState

from app.agents.ba_agent import ba_agent
from app.agents.router_agent import router_agent
from app.agents.sql_agent import sql_agent
from app.agents.rag_agent import rag_agent
from app.agents.validator_agent import validator_agent
from app.agents.governance_agent import governance_agent
from app.agents.executor_agent import executor_agent
from app.agents.reflection_agent import reflection_agent
from app.agents.explain_agent import explain_agent
from app.agents.audit_agent import audit_agent

logger = logging.getLogger(__name__)


def build_graph():

    graph = StateGraph(AgentState)

    # =============================
    # REGISTER ALL NODES
    # =============================
    graph.add_node("ba_agent", ba_agent)
    graph.add_node("router_agent", router_agent)
    graph.add_node("sql_agent", sql_agent)
    graph.add_node("rag_agent", rag_agent)
    graph.add_node("validator_agent", validator_agent)
    graph.add_node("governance_agent", governance_agent)
    graph.add_node("executor_agent", executor_agent)
    graph.add_node("reflection_agent", reflection_agent)
    graph.add_node("explain_agent", explain_agent)
    graph.add_node("audit_agent", audit_agent)

    # =============================
    # ENTRY
    # =============================
    graph.set_entry_point("ba_agent")
    graph.add_edge("ba_agent", "router_agent")

    # =============================
    # ROUTING: SQL vs RAG vs HYBRID
    # =============================
    def route_after_router(state: AgentState):
        route = (state.route or "SQL").upper()
        if route == "RAG":
            return "rag_agent"
        if route == "HYBRID":
            return "rag_agent"  # RAG first, then SQL in explain
        return "sql_agent"

    graph.add_conditional_edges(
        "router_agent",
        route_after_router,
        {
            "rag_agent": "rag_agent",
            "sql_agent": "sql_agent",
        }
    )

    # =============================
    # RAG PATH
    # HYBRID: RAG enriches context, then falls into SQL pipeline
    # Pure RAG: goes straight to explain
    # =============================
    def route_after_rag(state: AgentState):
        if (state.route or "").upper() == "HYBRID":
            return "sql_agent"
        return "explain_agent"

    graph.add_conditional_edges(
        "rag_agent",
        route_after_rag,
        {
            "sql_agent": "sql_agent",
            "explain_agent": "explain_agent",
        }
    )

    # =============================
    # SQL PIPELINE
    # =============================
    graph.add_edge("sql_agent", "validator_agent")
    graph.add_edge("validator_agent", "governance_agent")

    # =============================
    # GOVERNANCE GATE
    # =============================
    def route_after_governance(state: AgentState):
        if state.status == "BLOCKED":
            return "audit_agent"
        return "executor_agent"

    graph.add_conditional_edges(
        "governance_agent",
        route_after_governance,
        {
            "executor_agent": "executor_agent",
            "audit_agent": "audit_agent",
        }
    )

    # =============================
    # EXECUTION → EXPLAIN or REFLECT
    # =============================
    def route_after_execution(state: AgentState):
        if state.status == "EXECUTED":
            return "explain_agent"
        return "reflection_agent"

    graph.add_conditional_edges(
        "executor_agent",
        route_after_execution,
        {
            "explain_agent": "explain_agent",
            "reflection_agent": "reflection_agent",
        }
    )

    # =============================
    # REFLECTION LOOP (with max retry guard)
    # =============================
    def route_after_reflection(state: AgentState):
        if state.retry_count >= state.max_retries:
            logger.warning(f"Max retries reached for execution_id={state.execution_id}")
            return "audit_agent"
        if state.status == "RETRY":
            return "sql_agent"
        return "audit_agent"

    graph.add_conditional_edges(
        "reflection_agent",
        route_after_reflection,
        {
            "sql_agent": "sql_agent",
            "audit_agent": "audit_agent",
        }
    )

    # =============================
    # ALL PATHS CONVERGE TO AUDIT → END
    # =============================
    graph.add_edge("explain_agent", "audit_agent")
    graph.add_edge("audit_agent", END)

    return graph.compile()