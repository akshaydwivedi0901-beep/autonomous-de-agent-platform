import logging
from app.state.agent_state import AgentState
from app.orchestrator.llm_router import LLMRouter

logger = logging.getLogger(__name__)

EXPLAIN_PROMPT = """You are a helpful, concise data analyst assistant.

Answer the user's question using the SQL query results and/or knowledge context below.
Be business-friendly. If numbers are present, highlight the key insight clearly.
If both SQL results and knowledge context exist, synthesize them into a single coherent answer.

---
QUESTION: {question}

SQL RESULT ({row_count} rows):
{data_summary}

KNOWLEDGE CONTEXT:
{rag_context}

CONVERSATION HISTORY:
{history}
---

Provide a clear, direct answer. Do not repeat the question. Do not mention SQL or technical details unless asked."""


def _format_rows(rows) -> str:
    if not rows:
        return "No data returned."

    lines = []
    for i, row in enumerate(rows[:10]):  # cap at 10 for prompt size
        if isinstance(row, dict):
            lines.append(", ".join(f"{k}={v}" for k, v in row.items()))
        elif isinstance(row, (list, tuple)):
            lines.append(" | ".join(str(v) for v in row))
        else:
            lines.append(str(row))

    if len(rows) > 10:
        lines.append(f"... and {len(rows) - 10} more rows")

    return "\n".join(lines)


def _format_history(history: list) -> str:
    if not history:
        return "None"
    relevant = [
        m for m in history
        if m.get("role") in ("user", "assistant")
    ][-6:]
    return "\n".join(
        f"  {m.get('role', 'user').upper()}: {m.get('message', '')}"
        for m in relevant
    )


def explain_agent(state: AgentState) -> AgentState:

    try:
        logger.info(" EXPLAIN AGENT START")

        rows = state.rows or []
        rag_context = state.rag_context or ""
        question = state.question

        data_summary = _format_rows(rows)

        # =============================
        # NOTHING TO EXPLAIN
        # =============================
        if not rows and not rag_context:
            state.final_answer = (
                "I couldn't find any relevant data or knowledge for your question. "
                "Please try rephrasing."
            )
            state.explanation = state.final_answer
            state.status = "EXPLAINED"
            return state

        # =============================
        # LLM-POWERED ANSWER
        # =============================
        prompt = EXPLAIN_PROMPT.format(
            question=question,
            row_count=state.row_count or len(rows),
            data_summary=data_summary,
            rag_context=rag_context or "None",
            history=_format_history(state.conversation_history),
        )

        llm = LLMRouter.get_llm("explain", question)
        response = llm.invoke(prompt)

        state.final_answer = response.content.strip()
        state.explanation = state.final_answer
        state.status = "EXPLAINED"

        logger.info(" Explanation generated")

        return state

    except Exception:
        logger.exception("❌ EXPLAIN AGENT FAILED")

        # Graceful fallback — never crash the pipeline
        if state.rows:
            state.final_answer = _format_rows(state.rows)
        elif state.rag_context:
            state.final_answer = state.rag_context
        else:
            state.final_answer = "Unable to generate an answer at this time."

        state.explanation = state.final_answer
        state.status = "EXPLAINED"

        return state
