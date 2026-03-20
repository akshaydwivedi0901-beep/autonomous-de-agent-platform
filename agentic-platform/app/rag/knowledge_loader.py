# app/rag/knowledge_loader.py

from langchain_core.documents import Document
from app.rag.vector_store import get_vector_store
from app.services.schema_service import SchemaService

def load_knowledge():

    vector_store = get_vector_store()
    schema_service = SchemaService()

    metadata = schema_service.get_schema_metadata()

    documents = []

    # Load schema tables
    for table, columns in metadata["tables"].items():
        documents.append(
            Document(
                page_content=f"""
                Table: {table}
                Columns: {columns}
                """,
                metadata={
                    "type": "schema",
                    "table": table
                }
            )
        )

    # Example KPI (extend later)
    documents.append(
        Document(
            page_content="""
            KPI: Revenue
            Definition: Total billed revenue.
            Formula: SUM(revenue_amount)
            Usually located in fact tables.
            """,
            metadata={
                "type": "kpi",
                "name": "revenue"
            }
        )
    )

    vector_store.add_documents(documents)
    vector_store.persist()