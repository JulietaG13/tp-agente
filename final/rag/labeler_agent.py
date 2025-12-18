from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from langchain_core.messages import HumanMessage, SystemMessage

from final.agents import create_model


def _extract_json_object(text: str) -> dict:
    if isinstance(text, dict):
        return text
    try:
        return json.loads(text)
    except Exception:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    obj = re.search(r"\{[\s\S]*\}", text)
    if obj:
        return json.loads(obj.group(0))

    raise ValueError(f"Could not parse JSON object from: {text[:200]}")


def _normalize_subtopics(subtopics: Sequence[str]) -> list[str]:
    cleaned: list[str] = []
    seen = set()
    for s in subtopics:
        if not isinstance(s, str):
            continue
        val = " ".join(s.strip().split())
        if not val:
            continue
        key = val.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(val)
    return cleaned


@dataclass(frozen=True)
class ChunkForLabel:
    chunk_id: str
    text: str


class ChunkSubtopicLabeler:
    def __init__(self):
        self._llm = create_model()

    def extract_taxonomy(self, samples: Sequence[str], max_subtopics: int = 30) -> list[str]:
        system = SystemMessage(
            content=(
                "You extract a compact subtopic taxonomy from course material.\n"
                "Return ONLY valid JSON.\n"
                'Schema: {"subtopics": ["subtopic1", "subtopic2", ...]}\n'
                "Rules:\n"
                "- Subtopics must be short (2-6 words).\n"
                "- Avoid duplicates and overly generic items.\n"
                f"- Return between 8 and {max_subtopics} subtopics.\n"
            )
        )
        joined = "\n\n---\n\n".join(samples)
        human = HumanMessage(
            content=(
                "Extract subtopics from these excerpts:\n\n"
                f"{joined}\n\n"
                "Return JSON only."
            )
        )
        resp = self._llm.invoke([system, human])
        data = _extract_json_object(resp.content)
        return _normalize_subtopics(data.get("subtopics", []))[:max_subtopics]

    def label_chunks(
        self,
        chunks: Sequence[ChunkForLabel],
        taxonomy: Sequence[str],
        max_subtopics_per_chunk: int = 3,
    ) -> Mapping[str, list[str]]:
        if not chunks:
            return {}
        if not taxonomy:
            return {c.chunk_id: [] for c in chunks}

        system = SystemMessage(
            content=(
                "You label each chunk with one or more subtopics from the provided taxonomy.\n"
                "Return ONLY valid JSON.\n"
                'Schema: {"labels": [{"chunk_id": "...", "subtopics": ["..."]}]}\n'
                "Rules:\n"
                "- Use only subtopics from the taxonomy list.\n"
                f"- Assign 1 to {max_subtopics_per_chunk} subtopics per chunk.\n"
                "- If none match, return an empty list for that chunk.\n"
            )
        )

        taxonomy_block = "\n".join([f"- {t}" for t in taxonomy])
        chunk_block = "\n\n".join(
            [
                f"[chunk_id={c.chunk_id}]\n{c.text}"
                for c in chunks
            ]
        )
        human = HumanMessage(
            content=(
                "Taxonomy:\n"
                f"{taxonomy_block}\n\n"
                "Chunks:\n"
                f"{chunk_block}\n\n"
                "Return JSON only."
            )
        )

        resp = self._llm.invoke([system, human])
        data = _extract_json_object(resp.content)
        labels = data.get("labels", [])

        by_id: dict[str, list[str]] = {c.chunk_id: [] for c in chunks}
        for item in labels:
            chunk_id = item.get("chunk_id")
            if chunk_id in by_id:
                by_id[chunk_id] = _normalize_subtopics(item.get("subtopics", []))[:max_subtopics_per_chunk]
        return by_id


