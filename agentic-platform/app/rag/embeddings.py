from langchain_community.embeddings import FastEmbedEmbeddings


def get_embedding_model():
    return FastEmbedEmbeddings()