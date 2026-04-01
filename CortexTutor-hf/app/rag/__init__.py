"""RAG (Retrieval-Augmented Generation) module."""

from .splitter import split_transcript
from .embeddings import get_embeddings
from .vector_store import create_vector_store, save_vector_store, load_vector_store
from .retriever import create_retriever, retrieve_with_scores
from .pipeline import create_rag_chain, ask_question

__all__ = [
    "split_transcript",
    "get_embeddings",
    "create_vector_store",
    "save_vector_store",
    "load_vector_store",
    "create_retriever",
    "retrieve_with_scores",
    "create_rag_chain",
    "ask_question",
]
