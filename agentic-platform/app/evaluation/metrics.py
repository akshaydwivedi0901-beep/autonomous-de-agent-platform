from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "ai_requests_total",
    "Total number of AI requests"
)

QUERY_SUCCESS = Counter(
    "ai_query_success_total",
    "Successful AI responses"
)

QUERY_FAILURE = Counter(
    "ai_query_failure_total",
    "Failed AI responses"
)

AGENT_EXECUTION_TIME = Histogram(
    "agent_execution_seconds",
    "Agent execution latency"
)