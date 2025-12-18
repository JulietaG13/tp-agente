from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class RagContext:
    persist_directory: str
    collection_name: str
    subtopics: tuple[str, ...] = ()


_rag_context: ContextVar[Optional[RagContext]] = ContextVar("rag_context", default=None)


def set_rag_context(context: RagContext) -> None:
    _rag_context.set(context)


def get_rag_context() -> RagContext:
    context = _rag_context.get()
    if context is None:
        return RagContext(persist_directory="./chroma_db", collection_name="course_content", subtopics=())
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


