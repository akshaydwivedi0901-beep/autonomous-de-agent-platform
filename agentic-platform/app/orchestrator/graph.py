from langgraph.graph import StateGraph, END

from app.state.agent_state import AgentState

from app.agents.ba_agent import ba_agent
from app.agents.router_agent import router_agent
from app.agents.sql_agent import sql_agent
from app.agents.validator_agent import validator_agent
from app.agents.executor_agent import executor_agent
from app.agents.reflection_agent import reflection_agent
from app.agents.explain_agent import explain_agent


def build_graph():

    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("ba_agent", ba_agent)
    graph.add_node("router_agent", router_agent)
    graph.add_node("sql_agent", sql_agent)
    graph.add_node("validator_agent", validator_agent)
    graph.add_node("executor_agent", executor_agent)
    graph.add_node("reflection_agent", reflection_agent)
    graph.add_node("explain_agent", explain_agent)

    # Flow
    graph.set_entry_point("ba_agent")

    graph.add_edge("ba_agent", "router_agent")
    graph.add_edge("router_agent", "sql_agent")
    graph.add_edge("sql_agent", "validator_agent")
    graph.add_edge("validator_agent", "executor_agent")

    # Execution routing
    def route_after_execution(state: AgentState):
        if state.status == "EXECUTED":
            return "explain_agent"

        if state.status == "FAILED":
            return "reflection_agent"

        return END

    graph.add_conditional_edges(
        "executor_agent",
        route_after_execution,
        {
            "explain_agent": "explain_agent",
            "reflection_agent": "reflection_agent",
            END: END,
        },
    )

    # Reflection routing (loop control)
    def route_after_reflection(state: AgentState):
        if state.retry_count >= state.max_retries:
            return END

        if state.status == "RETRY":
            return "sql_agent"

        return END

    graph.add_conditional_edges(
        "reflection_agent",
        route_after_reflection,
        {
            "sql_agent": "sql_agent",
            END: END,
        },
    )

    graph.add_edge("explain_agent", END)

    return graph.compile()