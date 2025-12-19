from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence

from final.rag.indexer import ContentIndexer
from final.rag.labeler_agent import ChunkSubtopicLabeler
from final.rag.vector_store import ChromaVectorStore


@dataclass(frozen=True)
class IndexResult:
    subtopics: tuple[str, ...]
    chunk_ids: tuple[str, ...]


def _read_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def _build_chunk_ids(file_path: str, chunk_count: int) -> list[str]:
    base = os.path.basename(file_path)
    return [f"{base}_chunk_{i}" for i in range(chunk_count)]


def _select_taxonomy_samples(chunks: Sequence[str], max_samples: int = 7) -> list[str]:
    if not chunks:
        return []
    if len(chunks) <= max_samples:
        return list(chunks)

    picks: list[str] = []
    picks.append(chunks[0])
    if len(chunks) > 2:
        picks.append(chunks[1])
    mid = len(chunks) // 2
    picks.append(chunks[mid])
    if mid + 1 < len(chunks):
        picks.append(chunks[mid + 1])
    picks.append(chunks[-2])
    picks.append(chunks[-1])
    return picks[:max_samples]


def index_course_file(
    file_path: str,
    persist_directory: str = None,
    collection_name: str = "course_content",
    *,
    force_reset: bool = True,
    chunk_size: int = 400,
    overlap: int = 50,
    max_taxonomy_subtopics: int = 30,
) -> IndexResult:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    from final.rag.session_context import default_persist_directory
    persist_dir = persist_directory or default_persist_directory()

    vector_store = ChromaVectorStore(
        persist_directory=persist_dir,
        collection_name=collection_name,
    )
    if force_reset:
        vector_store.reset_collection()

    raw_text = _read_text(file_path)
    indexer = ContentIndexer(vector_store)
    chunk_pairs = indexer.chunk_text(raw_text, chunk_size=chunk_size, overlap=overlap)
    chunk_texts = [t for t, _ in chunk_pairs]
    chunk_ids = _build_chunk_ids(file_path, len(chunk_texts))

    labeler = ChunkSubtopicLabeler()
    samples = _select_taxonomy_samples(chunk_texts)
    taxonomy = labeler.extract_taxonomy(samples=samples, max_subtopics=max_taxonomy_subtopics)

    metadatas = []
    for i, (_, start_pos) in enumerate(chunk_pairs):
        metadatas.append(
            {
                "source": file_path,
                "chunk_index": i,
                "start_position": start_pos,
                "chunk_size": len(chunk_texts[i].split()),
            }
        )

    vector_store.add_documents(chunk_texts, metadatas, chunk_ids)

    return IndexResult(subtopics=tuple(taxonomy), chunk_ids=tuple(chunk_ids))


