import logging
import uuid
import json

from app.state.agent_state import AgentState
from app.orchestrator.llm_router import LLMRouter
from app.rag.retriever import retrieve_context

logger = logging.getLogger(__name__)


def safe_json_parse(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def ba_agent(state: AgentState):
    try:
        logger.info(" BA AGENT START")

        # =============================
        # INIT
        # =============================
        if not getattr(state, "execution_id", None):
            state.execution_id = str(uuid.uuid4())

        question = state.question

        llm = LLMRouter.get_llm("planner", question)

        # =============================
        # RAG (safe)
        # =============================
        try:
            rag_context = retrieve_context(question)
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            rag_context = ""

        state.rag_context = str(rag_context)

        # =============================
        # PROMPT
        # =============================
        prompt = f"""
You are a Business Analyst.

Return ONLY valid JSON.

Question:
{question}

Format:
{{
  "metric": "",
  "filters": [],
  "tables": [],
  "columns": []
}}
"""

        # =============================
        # LLM CALL
        # =============================
        response = llm.invoke(prompt)
        raw_output = response.content.strip()

        logger.info(f"BA RAW OUTPUT:\n{raw_output}")

        # =============================
        # SAFE PARSING
        # =============================
        parsed = safe_json_parse(raw_output)

        if not parsed:
            logger.warning(" BA JSON parse failed, using fallback")

            parsed = {
                "metric": "unknown",
                "filters": [],
                "tables": [],
                "columns": []
            }

        state.business_analysis = parsed
        state.status = "BA_COMPLETE"

        return state

    except Exception as e:
        logger.exception(" BA Agent failed")

        #  NEVER BREAK FLOW
        state.business_analysis = {
            "metric": "fallback",
            "filters": [],
            "tables": [],
            "columns": []
        }

        state.status = "BA_FAILED"
        state.error = str(e)

        return state