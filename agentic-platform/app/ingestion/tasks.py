from app.rag.knowledge_loader import load_documents
from app.rag.vector_store import get_vector_store


def process_document(file_path):

    docs = load_documents(file_path)

    vector_store = get_vector_store()

    vector_store.add_documents(docs)

    print("Document indexed:", file_path)
