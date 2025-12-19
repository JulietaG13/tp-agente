from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Optional, Sequence, Any


@dataclass(frozen=True)
class RagContext:
    persist_directory: str
    collection_name: str
    subtopics: tuple[str, ...] = ()


_rag_context: ContextVar[Optional[RagContext]] = ContextVar("rag_context", default=None)
_last_retrieved_chunk_ids: ContextVar[tuple[str, ...]] = ContextVar("last_retrieved_chunk_ids", default=())
_rag_components: ContextVar[Optional[tuple[str, str, Any, Any]]] = ContextVar("rag_components", default=None)
_global_rag_context: Optional[RagContext] = None
_global_components_lock = Lock()
_global_components_cache: dict[tuple[str, str], tuple[Any, Any]] = {}

def default_persist_directory() -> str:
    return str(Path(__file__).resolve().parents[2] / "chroma_db")


def set_rag_context(context: RagContext) -> None:
    global _global_rag_context
    _rag_context.set(context)
    _rag_components.set(None)
    _global_rag_context = context


def get_rag_context() -> RagContext:
    context = _rag_context.get()
    if context is None:
        if _global_rag_context is not None:
            return _global_rag_context
        return RagContext(persist_directory=default_persist_directory(), collection_name="course_content", subtopics=())
    return context


def set_rag_subtopics(subtopics: Sequence[str]) -> None:
    context = get_rag_context()
    set_rag_context(
        RagContext(
            persist_directory=context.persist_directory,
            collection_name=context.collection_name,
            subtopics=tuple(subtopics),
        )
    )


def record_retrieved_chunk_ids(chunk_ids: Sequence[str]) -> None:
    _last_retrieved_chunk_ids.set(tuple([str(x) for x in chunk_ids if x]))


def get_last_retrieved_chunk_ids() -> tuple[str, ...]:
    return _last_retrieved_chunk_ids.get()


def clear_last_retrieved_chunk_ids() -> None:
    _last_retrieved_chunk_ids.set(())


def get_rag_components_cached():
    """
    Returns (vector_store, retriever) for the current RagContext, caching per session/context.
    Cache is invalidated automatically on set_rag_context().
    """
    ctx = get_rag_context()
    key = (ctx.persist_directory, ctx.collection_name)

    cached = _rag_components.get()
    if cached is not None:
        persist_directory, collection_name, vector_store, retriever = cached
        if (persist_directory, collection_name) == key:
            return vector_store, retriever

    with _global_components_lock:
        pair = _global_components_cache.get(key)
        if pair is None:
            from final.rag.vector_store import ChromaVectorStore
            from final.rag.retriever import ContentRetriever

            vector_store = ChromaVectorStore(
                persist_directory=ctx.persist_directory,
                collection_name=ctx.collection_name,
            )
            retriever = ContentRetriever(vector_store)
            pair = (vector_store, retriever)
            _global_components_cache[key] = pair

    vector_store, retriever = pair
    _rag_components.set((ctx.persist_directory, ctx.collection_name, vector_store, retriever))
    return vector_store, retriever


def clear_rag_components_cache(persist_directory: Optional[str] = None, collection_name: Optional[str] = None) -> None:
    """
    Clears the process-wide RAG components cache.
    Useful if you reset/reindex a collection and want a fresh vector store instance.
    """
    with _global_components_lock:
        if persist_directory is None and collection_name is None:
            _global_components_cache.clear()
            return

        to_delete = []
        for (p, c) in _global_components_cache.keys():
            if persist_directory is not None and p != persist_directory:
                continue
            if collection_name is not None and c != collection_name:
                continue
            to_delete.append((p, c))
        for k in to_delete:
            _global_components_cache.pop(k, None)


