import pytest
import uuid
from unittest.mock import patch, MagicMock
from app.state.agent_state import AgentState


def make_state(**kwargs):
    defaults = {"question": "how many orders were placed in 1995?", "environment": "dev"}
    defaults.update(kwargs)
    return AgentState(**defaults)


def mock_llm(content):
    r = MagicMock()
    r.content = content
    r.usage_metadata = {"input_tokens": 500, "output_tokens": 50}
    r.last_metrics = None
    return r


class TestAgentState:
    def test_auto_generates_execution_id(self):
        s = make_state()
        assert s.execution_id is not None and len(s.execution_id) == 36

    def test_unique_session_ids(self):
        assert make_state().session_id != make_state().session_id

    def test_defaults(self):
        s = make_state()
        assert s.retry_count == 0
        assert s.max_retries == 2
        assert s.route is None
        assert s.conversation_history == []


class TestRouterAgent:
    def test_sql_keywords_route_sql(self):
        from app.agents.router_agent import router_agent
        assert router_agent(make_state(question="total revenue 1996?")).route == "SQL"

    def test_rag_keywords_route_rag(self):
        from app.agents.router_agent import router_agent
        r = router_agent(make_state(question="what is the definition of revenue?")).route
        assert r in ("RAG", "HYBRID")

    def test_never_crashes(self):
        from app.agents.router_agent import router_agent
        assert router_agent(make_state(question="")).route is not None

    @pytest.mark.parametrize("q,expected", [
        ("count orders", ["SQL"]),
        ("total sales 1995", ["SQL"]),
        ("what is a KPI", ["RAG", "HYBRID"]),
        ("define revenue", ["RAG", "HYBRID"]),
    ])
    def test_parametrized(self, q, expected):
        from app.agents.router_agent import router_agent
        assert router_agent(make_state(question=q)).route in expected


VALID_SQL = "SELECT C_NAME FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER WHERE C_CUSTKEY = 1"

class TestValidatorAgent:
    def test_valid_passes(self):
        from app.agents.validator_agent import validator_agent
        assert validator_agent(make_state(generated_sql=VALID_SQL)).validation_status == "VALID"

    def test_limit_added(self):
        from app.agents.validator_agent import validator_agent
        r = validator_agent(make_state(generated_sql=VALID_SQL))
        assert "LIMIT" in r.validated_sql.upper()

    def test_semicolon_removed(self):
        from app.agents.validator_agent import validator_agent
        r = validator_agent(make_state(generated_sql=VALID_SQL + ";"))
        assert not r.validated_sql.strip().endswith(";")

    def test_existing_limit_not_duplicated(self):
        from app.agents.validator_agent import validator_agent
        r = validator_agent(make_state(generated_sql=VALID_SQL + " LIMIT 5"))
        assert r.validated_sql.upper().count("LIMIT") == 1

    @pytest.mark.parametrize("sql", [
        "DROP TABLE CUSTOMER",
        "DELETE FROM ORDERS WHERE 1=1",
        "TRUNCATE TABLE LINEITEM",
        "UPDATE CUSTOMER SET C_NAME='x'",
        "INSERT INTO ORDERS VALUES (1,2,3)",
    ])
    def test_dangerous_sql_blocked(self, sql):
        from app.agents.validator_agent import validator_agent
        assert validator_agent(make_state(generated_sql=sql)).validation_status == "INVALID"

    def test_select_star_blocked(self):
        from app.agents.validator_agent import validator_agent
        assert validator_agent(make_state(generated_sql="SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER")).validation_status == "INVALID"

    def test_empty_sql_blocked(self):
        from app.agents.validator_agent import validator_agent
        assert validator_agent(make_state(generated_sql="")).validation_status == "INVALID"

    def test_none_sql_blocked(self):
        from app.agents.validator_agent import validator_agent
        assert validator_agent(make_state(generated_sql=None)).validation_status == "INVALID"


class TestReflectionAgent:
    def test_increments_retry(self):
        from app.agents.reflection_agent import reflection_agent
        r = reflection_agent(make_state(status="EXECUTION_FAILED", retry_count=0))
        assert r.retry_count == 1 and r.status == "RETRY"

    def test_stops_at_max(self):
        from app.agents.reflection_agent import reflection_agent
        r = reflection_agent(make_state(retry_count=2, max_retries=2))
        assert r.status == "FAILED" and r.final_answer is not None

    def test_never_exceeds_max(self):
        from app.agents.reflection_agent import reflection_agent
        r = reflection_agent(make_state(retry_count=10, max_retries=2))
        assert r.status == "FAILED"


SAFE_SQL = "SELECT COUNT(O_ORDERKEY) FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS WHERE O_ORDERDATE > '1995-01-01'"

class TestGovernanceAgent:
    def test_clean_sql_approved(self):
        from app.agents.governance_agent import governance_agent
        r = governance_agent(make_state(generated_sql=SAFE_SQL, environment="dev", execution_id=str(uuid.uuid4())))
        assert r.governance_status == "APPROVED"

    @pytest.mark.parametrize("sql", ["DROP TABLE ORDERS", "TRUNCATE TABLE LINEITEM"])
    def test_dangerous_blocked(self, sql):
        from app.agents.governance_agent import governance_agent
        r = governance_agent(make_state(generated_sql=sql, environment="dev", execution_id=str(uuid.uuid4())))
        assert r.status == "BLOCKED"

    def test_risk_score_set(self):
        from app.agents.governance_agent import governance_agent
        r = governance_agent(make_state(generated_sql=SAFE_SQL, environment="dev", execution_id=str(uuid.uuid4())))
        assert r.risk_score is not None and r.risk_score >= 0


class TestExplainAgent:
    def test_no_data_graceful(self):
        from app.agents.explain_agent import explain_agent
        with patch("app.agents.explain_agent.LLMRouter") as mr:
            ml = MagicMock()
            ml.invoke.return_value = mock_llm("No data.")
            ml.last_metrics = None
            mr.get_llm.return_value = ml
            r = explain_agent(make_state(rows=None, rag_context=None))
            assert r.status == "EXPLAINED"

    def test_llm_error_fallback(self):
        from app.agents.explain_agent import explain_agent
        with patch("app.agents.explain_agent.LLMRouter") as mr:
            ml = MagicMock()
            ml.invoke.side_effect = Exception("timeout")
            mr.get_llm.return_value = ml
            r = explain_agent(make_state(rows=[{"TOTAL": 42}], row_count=1))
            assert r.status == "EXPLAINED" and r.final_answer is not None


class TestComplexityScorer:
    def test_simple_scores_low(self):
        from app.orchestrator.llm_router import score_query_complexity
        r = score_query_complexity("how many orders?")
        assert r.score <= 40 and r.tier in ("nano", "small")

    def test_complex_scores_high(self):
        from app.orchestrator.llm_router import score_query_complexity
        r = score_query_complexity("running total cumulative year over year growth rate window function")
        assert r.score >= 50

    def test_score_capped_at_100(self):
        from app.orchestrator.llm_router import score_query_complexity
        r = score_query_complexity("running total cumulative window lag lead percentile rank join join join customer order supplier nation region")
        assert r.score <= 100


class TestCacheService:
    def test_key_deterministic(self):
        from app.services.cache_service import CacheService
        assert CacheService._query_key("orders 1995?", "prod") == CacheService._query_key("orders 1995?", "prod")

    def test_different_env_different_key(self):
        from app.services.cache_service import CacheService
        assert CacheService._query_key("q", "prod") != CacheService._query_key("q", "dev")

    def test_normalises_case(self):
        from app.services.cache_service import CacheService
        assert CacheService._query_key("How Many Orders?", "prod") == CacheService._query_key("how many orders?", "prod")


class TestHealthAPI:
    def test_returns_ok(self):
        from app.api.health_api import health
        r = health()
        assert r["status"] == "ok" and r["service"] == "ai-agent"


class TestIntegration:
    def test_validator_governance_happy_path(self):
        from app.agents.validator_agent import validator_agent
        from app.agents.governance_agent import governance_agent
        s = make_state(generated_sql=SAFE_SQL, execution_id=str(uuid.uuid4()), environment="dev")
        s = validator_agent(s)
        assert s.validation_status == "VALID"
        s = governance_agent(s)
        assert s.governance_status == "APPROVED"

    def test_reflection_loop_stops(self):
        from app.agents.reflection_agent import reflection_agent
        s = make_state(status="EXECUTION_FAILED", retry_count=0, max_retries=2)
        s = reflection_agent(s)
        assert s.retry_count == 1
        s.status = "EXECUTION_FAILED"
        s = reflection_agent(s)
        assert s.retry_count == 2
        s.status = "EXECUTION_FAILED"
        s = reflection_agent(s)
        assert s.status == "FAILED"
