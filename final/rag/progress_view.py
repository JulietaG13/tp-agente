from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from services.service_manager import get_service


@dataclass(frozen=True)
class ChunkProgress:
    attempts: int
    correct: int
    incorrect: int
    last_seen_turn: int | None
    last_correct_turn: int | None
    last_incorrect_turn: int | None


def get_chunk_progress(chunk_id: str) -> ChunkProgress:
    service = get_service()
    p = service.get_chunk_progress(chunk_id)
    return ChunkProgress(
        attempts=int(p.get("attempts", 0) or 0),
        correct=int(p.get("correct", 0) or 0),
        incorrect=int(p.get("incorrect", 0) or 0),
        last_seen_turn=p.get("last_seen_turn"),
        last_correct_turn=p.get("last_correct_turn"),
        last_incorrect_turn=p.get("last_incorrect_turn"),
    )


def is_mastered(progress: ChunkProgress) -> bool:
    if progress.attempts < 2:
        return False
    if progress.incorrect > 0:
        return False
    return progress.correct == progress.attempts


def chunk_guidance(progress: ChunkProgress) -> str:
    if is_mastered(progress):
        return "avoid_reusing_if_possible"
    if progress.attempts > 0 and progress.incorrect > 0:
        return "good_candidate_for_remediation_but_respect_cooldown"
    return "good_candidate_for_coverage"


def chunk_progress_payload(progress: ChunkProgress) -> dict:
    status = "new"
    if is_mastered(progress):
        status = "mastered"
    elif progress.attempts > 0 and progress.incorrect > 0:
        status = "needs_review"
    elif progress.attempts > 0 and progress.correct > 0:
        status = "in_progress"

    return {
        "chunk_status": status,
        "attempts": progress.attempts,
        "correct": progress.correct,
        "incorrect": progress.incorrect,
        "last_seen_turn": progress.last_seen_turn,
        "last_correct_turn": progress.last_correct_turn,
        "last_incorrect_turn": progress.last_incorrect_turn,
        "guidance": chunk_guidance(progress),
    }


def _subtopic_sort_key(per_sub: dict, subtopic: str) -> tuple[int, int]:
    key = " ".join(subtopic.strip().split()).casefold()
    p = per_sub.get(key, {})
    attempts = int(p.get("attempts", 0) or 0)
    incorrect = int(p.get("incorrect", 0) or 0)
    return (incorrect, -attempts)


def select_target_subtopics(
    all_subtopics: Sequence[str],
    *,
    max_topics: int = 2,
    cooldown_recent_questions: int = 3,
) -> list[str]:
    service = get_service()
    per_sub = service.list_subtopic_progress()
    recent = set(
        [" ".join(s.strip().split()).casefold() for s in service.get_recent_question_subtopics(cooldown_recent_questions)]
    )

    def rank(subtopic: str) -> tuple[int, int, int]:
        key = " ".join(subtopic.strip().split()).casefold()
        p = per_sub.get(key, {})
        attempts = int(p.get("attempts", 0) or 0)
        incorrect = int(p.get("incorrect", 0) or 0)
        last_seen = p.get("last_seen_turn")
        current_turn = getattr(service, "get_current_turn", lambda: 0)()
        age = (current_turn - last_seen) if isinstance(last_seen, int) else 10_000
        in_cooldown = 1 if key in recent else 0
        return (in_cooldown, -incorrect, attempts, -age)

    candidates = [s for s in all_subtopics if isinstance(s, str) and s.strip()]
    ordered = sorted(candidates, key=rank)
    chosen: list[str] = []
    seen = set()
    for s in ordered:
        k = " ".join(s.strip().split()).casefold()
        if k in seen:
            continue
        seen.add(k)
        chosen.append(s)
        if len(chosen) >= max_topics:
            break
    return chosen


def build_subtopic_focus_brief(subtopics: Sequence[str], max_items: int = 20) -> str:
    service = get_service()
    per_sub = service.list_subtopic_progress()
    ordered = sorted(list(subtopics), key=lambda s: _subtopic_sort_key(per_sub, s), reverse=True)[:max_items]
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


