from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from services.service_manager import get_service


def _is_mastered(attempts: int, correct: int, incorrect: int) -> bool:
    if attempts < 2:
        return False
    if incorrect > 0:
        return False
    return correct == attempts


def build_chunk_progress_note(chunk_id: str) -> str:
    service = get_service()
    p = service.get_chunk_progress(chunk_id)
    attempts = int(p.get("attempts", 0) or 0)
    correct = int(p.get("correct", 0) or 0)
    incorrect = int(p.get("incorrect", 0) or 0)
    last_seen = p.get("last_seen_turn")

    status = "new"
    if _is_mastered(attempts, correct, incorrect):
        status = "mastered"
    elif attempts > 0 and incorrect > 0:
        status = "needs_review"
    elif attempts > 0 and correct > 0:
        status = "in_progress"

    parts = [
        f"chunk_status={status}",
        f"attempts={attempts}",
        f"correct={correct}",
        f"incorrect={incorrect}",
        f"last_seen_turn={last_seen}",
    ]
    if status == "mastered":
        parts.append("guidance=avoid_reusing_if_possible")
    elif status == "needs_review":
        parts.append("guidance=good_candidate_for_remediation_but_respect_cooldown")
    else:
        parts.append("guidance=good_candidate_for_coverage")
    return " | ".join(parts)


def build_subtopic_focus_brief(subtopics: Sequence[str], max_items: int = 20) -> str:
    service = get_service()
    per_sub = service.list_subtopic_progress()

    def score(subtopic: str) -> tuple[int, int]:
        key = " ".join(subtopic.strip().split()).casefold()
        p = per_sub.get(key, {})
        attempts = int(p.get("attempts", 0) or 0)
        incorrect = int(p.get("incorrect", 0) or 0)
        return (incorrect, -attempts)

    ordered = sorted(list(subtopics), key=score, reverse=True)[:max_items]
    lines = ["SUBTOPIC_FOCUS:"]
    for s in ordered:
        key = " ".join(s.strip().split()).casefold()
        p = per_sub.get(key, {})
        attempts = int(p.get("attempts", 0) or 0)
        correct = int(p.get("correct", 0) or 0)
        incorrect = int(p.get("incorrect", 0) or 0)
        last_incorrect = p.get("last_incorrect_turn")
        lines.append(
            f"- {s} | attempts={attempts} correct={correct} incorrect={incorrect} last_incorrect_turn={last_incorrect}"
        )
    return "\n".join(lines)


