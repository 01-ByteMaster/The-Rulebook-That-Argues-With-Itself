"""
Threshold tuning script.
Runs all test questions through retrieval and logs their top-1 scores,
then suggests an optimal NOT_COVERED_THRESHOLD.
"""

import sys
import os

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.ingest import load_corpus
from backend.retrieval import TFIDFRetriever
from backend.config import CORPUS_DIR

# -- Test Questions --

# TS-1: Not-covered questions (should score LOW)
NOT_COVERED_QUESTIONS = [
    "What are the library opening hours on weekends?",
    "Where can I park my car on campus?",
    "How do I connect to the campus WiFi network?",
    "What is the dress code for students on campus?",
    "Can I bring my pet to the university campus?",
    "How do I join a student club or society?",
    "What sports facilities are available on campus?",
    "Is there a counseling or mental health service on campus?",
    "What is the process for changing my major or program?",
    "How do I apply for an internship through the university?",
    "What are the rules for using the university gymnasium?",
    "Can I take a gap year and return to my program later?",
    "Where is the nearest ATM on campus?",
    "How do I get a duplicate ID card if I lose mine?",
    "What vaccinations are required before enrollment?",
    "Are students allowed to use drones on campus?",
    "How do I request a letter of recommendation from a professor?",
    "What is the policy on academic plagiarism for coursework?",
    "Can I audit a course without registering for credit?",
    "What transportation options are available from campus to the city center?",
    "How do I report a case of ragging or bullying?",
    "What are the rules for organizing an event on campus?",
    "Is there a student exchange program with foreign universities?",
    "How do I access the university's online learning portal?",
    "What is the procedure for obtaining a bonafide certificate?",
]

# TS-2: Conflict questions (should score HIGH and trigger conflict)
CONFLICT_QUESTIONS = [
    "What is the minimum attendance percentage I need to sit my exam?",
    "If I leave the hostel early, when do I get my deposit back?",
    "What GPA do I need to keep my scholarship?",
]

# TS-3: Answered questions (should score HIGH and answer normally)
ANSWERED_QUESTIONS = [
    "How is attendance percentage calculated?",
    "What happens if I am caught cheating in an exam?",
    "What is the hostel curfew time on weekdays?",
    "Are visitors allowed in hostel rooms?",
    "When is the semester fee payment deadline?",
    "How do I apply for a medical exemption for attendance?",
    "What is the late fee for paying tuition after the deadline?",
]

def main():
    print("=" * 70)
    print("THRESHOLD TUNING -- Score Distribution Analysis")
    print("=" * 70)

    # Load corpus and build index
    chunks = load_corpus(CORPUS_DIR)
    retriever = TFIDFRetriever(chunks)

    print("\n" + "-" * 70)
    print("TS-1: NOT-COVERED QUESTIONS (should score LOW)")
    print("-" * 70)
    nc_scores = []
    for i, q in enumerate(NOT_COVERED_QUESTIONS, 1):
        results = retriever.search(q, top_k=1)
        score = results[0].score if results else 0.0
        nc_scores.append(score)
        marker = "[!HIGH]" if score > 0.15 else "[OK]   "
        print(f"  {i:2d}. [{score:.4f}] {marker} {q[:60]}")

    print(f"\n  NOT-COVERED: min={min(nc_scores):.4f}, max={max(nc_scores):.4f}, "
          f"mean={sum(nc_scores)/len(nc_scores):.4f}")

    print("\n" + "-" * 70)
    print("TS-2: CONFLICT QUESTIONS (should score HIGH)")
    print("-" * 70)
    cf_scores = []
    for i, q in enumerate(CONFLICT_QUESTIONS, 1):
        results = retriever.search(q, top_k=10)
        score = results[0].score if results else 0.0
        cf_scores.append(score)

        # Check conflict detection
        from backend.classify import classify
        classification = classify(results)
        status = "[OK CONFLICT]" if classification["type"] == "conflict" else f"[FAIL {classification['type']}]"
        print(f"  {i}. [{score:.4f}] {status} -- {q}")

        if classification["type"] == "conflict":
            for p in classification["passages"]:
                print(f"       -> {p.section_id} ({p.source_file}) score={p.score:.4f}")
        else:
            print(f"       -> Top result: {results[0].section_id} ({results[0].source_file})")
            # Show conflict group chunks in top results
            for r in results[:5]:
                cg = r.conflict_group or "null"
                print(f"          {r.section_id} score={r.score:.4f} cg={cg}")

    print("\n" + "-" * 70)
    print("TS-3: ANSWERED QUESTIONS (should score HIGH)")
    print("-" * 70)
    ans_scores = []
    for i, q in enumerate(ANSWERED_QUESTIONS, 1):
        results = retriever.search(q, top_k=5)
        score = results[0].score if results else 0.0
        ans_scores.append(score)
        section = results[0].section_id if results else "N/A"
        print(f"  {i}. [{score:.4f}] {section} -- {q}")

    print(f"\n  ANSWERED: min={min(ans_scores):.4f}, max={max(ans_scores):.4f}, "
          f"mean={sum(ans_scores)/len(ans_scores):.4f}")

    # Threshold recommendation
    print("\n" + "=" * 70)
    print("THRESHOLD RECOMMENDATION")
    print("=" * 70)

    gap_low = max(nc_scores)
    gap_high = min(min(cf_scores), min(ans_scores))
    recommended = (gap_low + gap_high) / 2

    print(f"  Not-covered max score: {gap_low:.4f}")
    print(f"  Covered min score:     {gap_high:.4f}")
    print(f"  Gap:                   {gap_high - gap_low:.4f}")
    print(f"  --> Recommended NOT_COVERED_THRESHOLD: {recommended:.4f}")

    if gap_high > gap_low:
        print(f"  [OK] Clean separation exists! Set threshold to ~{recommended:.2f}")
    else:
        print(f"  [WARN] Overlap detected -- some questions may need rewording")

    # Also check RELEVANCE_FLOOR for conflict detection
    print(f"\n  --> Recommended RELEVANCE_FLOOR: {recommended * 0.7:.4f}")


if __name__ == "__main__":
    main()
