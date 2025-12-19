from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Sequence

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
                f"- Return as many as are clearly present, up to {max_subtopics}.\n"
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


