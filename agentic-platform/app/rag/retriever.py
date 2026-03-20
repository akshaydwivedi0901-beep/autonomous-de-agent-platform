# app/rag/retriever.py

from app.rag.vector_store import get_vector_store
from app.core.config import settings


def retrieve_context(query: str, k: int = 4):
    """
    Enterprise retrieval logic.

    Retrieval priority:
    1. KPI context
    2. Schema context
    3. General business docs
    """

    vector_store = get_vector_store()

    query_lower = query.lower()

    docs = []

    # ----------------------------
    # KPI retrieval
    # ----------------------------

    if "revenue" in query_lower or "kpi" in query_lower:

        kpi_docs = vector_store.similarity_search(
            query,
            k=2,
            filter={"type": "kpi"}
        )

        docs.extend(kpi_docs)

    # ----------------------------
    # Schema retrieval
    # ----------------------------

    schema_docs = vector_store.similarity_search(
        query,
        k=2,
        filter={"type": "schema"}
    )

    docs.extend(schema_docs)

    # ----------------------------
    # General document retrieval
    # ----------------------------

    general_docs = vector_store.similarity_search(
        query,
        k=k
    )

    docs.extend(general_docs)

    # ----------------------------
    # Remove duplicates
    # ----------------------------

    unique_docs = []
    seen = set()

    for doc in docs:
        content = doc.page_content

        if content not in seen:
            unique_docs.append(doc)
            seen.add(content)

    # ----------------------------
    # No context fallback
    # ----------------------------

    if not unique_docs:

        return {
            "context": "No relevant knowledge found in vector DB.",
            "source": "vector_db_empty"
        }

    context = "\n\n".join([doc.page_content for doc in unique_docs])

    return {
        "context": context,
        "source": "vector_db"
    }