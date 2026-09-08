"""
Classification module.
Implements the priority-ordered decision logic: conflict → not_covered → answered.
"""

from backend.retrieval import RetrievalResult
from backend.config import NOT_COVERED_THRESHOLD, RELEVANCE_FLOOR


def classify(top_k_results: list[RetrievalResult]) -> dict:
    """
    Classify the question based on retrieved chunks.
    Priority: conflict → not_covered → answered.

    Returns a dict with:
        - type: 'conflict' | 'not_covered' | 'answered'
        - passages: list of RetrievalResult
        - conflict_note: str or None
        - answer_passages: list of RetrievalResult (for answer generation)
    """

    if not top_k_results:
        return {
            "type": "not_covered",
            "passages": [],
            "conflict_note": None,
            "answer_passages": []
        }

    # Step 1: CONFLICT CHECK
    # Runs first — a conflicting topic is technically "covered" by the corpus,
    # just contradictorily, so it must be caught before not_covered check would
    # wrongly dismiss it, and before answered fallback would wrongly pick one side.
    relevant = [r for r in top_k_results if r.score >= RELEVANCE_FLOOR]

    groups_present: dict[str, list[RetrievalResult]] = {}
    for r in relevant:
        if r.conflict_group:  # not None/null
            groups_present.setdefault(r.conflict_group, []).append(r)

    for group_id, members in groups_present.items():
        if len(members) >= 2:
            # Found a conflict — return all members of this group
            section_ids = [m.section_id for m in members]
            return {
                "type": "conflict",
                "passages": members,
                "conflict_note": (
                    f"Sections {section_ids} give different answers on this topic. "
                    f"These sections belong to conflict group '{group_id}' and contain "
                    f"contradictory information."
                ),
                "answer_passages": []
            }

    # Step 2: NOT COVERED CHECK
    # If the best matching chunk's score is below the threshold,
    # the corpus doesn't meaningfully cover this topic.
    if top_k_results[0].score < NOT_COVERED_THRESHOLD:
        return {
            "type": "not_covered",
            "passages": [],  # don't send irrelevant passages that scored below threshold
            "conflict_note": None,
            "answer_passages": []
        }

    # Step 3: ANSWERED (default)
    # The corpus covers the topic and no conflict was found.
    return {
        "type": "answered",
        "passages": top_k_results,
        "conflict_note": None,
        "answer_passages": [r for r in top_k_results if r.score >= RELEVANCE_FLOOR]
    }
