"""
Full test suite runner.
Runs all test questions and generates test_results.md.
"""

import sys
import os
import json

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.ingest import load_corpus
from backend.retrieval import TFIDFRetriever
from backend.classify import classify
from backend.generate import generate_answer
from backend.config import CORPUS_DIR, TOP_K

# -- All Test Questions --
TEST_CASES = [
    # TS-1: Not-covered (25 questions)
    {"q": "What are the library opening hours on weekends?", "expected": "not_covered"},
    {"q": "Where can I park my car on campus?", "expected": "not_covered"},
    {"q": "How do I connect to the campus WiFi network?", "expected": "not_covered"},
    {"q": "What is the dress code for students on campus?", "expected": "not_covered"},
    {"q": "Can I bring my pet to the university campus?", "expected": "not_covered"},
    {"q": "How do I join a student club or society?", "expected": "not_covered"},
    {"q": "What sports facilities are available on campus?", "expected": "not_covered"},
    {"q": "Is there a counseling or mental health service on campus?", "expected": "not_covered"},
    {"q": "What is the process for changing my major or program?", "expected": "not_covered"},
    {"q": "How do I apply for an internship through the university?", "expected": "not_covered"},
    {"q": "What are the rules for using the university gymnasium?", "expected": "not_covered"},
    {"q": "Can I take a gap year and return to my program later?", "expected": "not_covered"},
    {"q": "Where is the nearest ATM on campus?", "expected": "not_covered"},
    {"q": "Where can I find the lost-and-found office on campus?", "expected": "not_covered"},
    {"q": "What vaccinations are required before enrollment?", "expected": "not_covered"},
    {"q": "Are students allowed to use drones on campus?", "expected": "not_covered"},
    {"q": "How do I request a letter of recommendation from a professor?", "expected": "not_covered"},
    {"q": "What is the policy on academic plagiarism for coursework?", "expected": "not_covered"},
    {"q": "Does the university have a swimming pool?", "expected": "not_covered"},
    {"q": "What transportation options are available from campus to the city center?", "expected": "not_covered"},
    {"q": "How do I report a case of ragging or bullying?", "expected": "not_covered"},
    {"q": "What are the rules for organizing an event on campus?", "expected": "not_covered"},
    {"q": "Is there a student exchange program with foreign universities?", "expected": "not_covered"},
    {"q": "How do I access the university's online learning portal?", "expected": "not_covered"},
    {"q": "What is the procedure for obtaining a bonafide certificate?", "expected": "not_covered"},

    # TS-2: Conflict (3 questions)
    {"q": "What is the minimum attendance percentage I need to sit my exam?", "expected": "conflict"},
    {"q": "If I leave the hostel early, when do I get my deposit back?", "expected": "conflict"},
    {"q": "What GPA do I need to keep my scholarship?", "expected": "conflict"},

    # TS-3: Answered (7 questions)
    {"q": "How is attendance percentage calculated?", "expected": "answered"},
    {"q": "What happens if I use unfair means during an examination?", "expected": "answered"},
    {"q": "What is the hostel curfew time on weekdays?", "expected": "answered"},
    {"q": "Are visitors allowed in hostel rooms?", "expected": "answered"},
    {"q": "When is the semester fee payment deadline?", "expected": "answered"},
    {"q": "How do I submit a maintenance complaint for my hostel room?", "expected": "answered"},
    {"q": "What is the late fee for paying tuition after the deadline?", "expected": "answered"},
]


def main():
    print("=" * 70)
    print("FULL TEST SUITE")
    print("=" * 70)

    # Load corpus and build index
    chunks = load_corpus(CORPUS_DIR)
    retriever = TFIDFRetriever(chunks)

    results_rows = []
    pass_count = 0
    fail_count = 0

    for i, tc in enumerate(TEST_CASES, 1):
        question = tc["q"]
        expected = tc["expected"]

        # Run the pipeline
        search_results = retriever.search(question, top_k=TOP_K)
        classification = classify(search_results)
        actual = classification["type"]

        passed = actual == expected
        if passed:
            pass_count += 1
            status = "PASS"
        else:
            fail_count += 1
            status = "FAIL"

        top_score = search_results[0].score if search_results else 0.0
        print(f"  {i:2d}. [{status}] expected={expected:12s} actual={actual:12s} "
              f"score={top_score:.4f} -- {question[:55]}")

        results_rows.append({
            "num": i,
            "question": question,
            "expected": expected,
            "actual": actual,
            "pass_fail": "PASS" if passed else "FAIL",
            "top_score": f"{top_score:.4f}"
        })

    print(f"\n  TOTAL: {pass_count} passed, {fail_count} failed out of {len(TEST_CASES)}")

    # Generate test_results.md
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    output_path = os.path.join(data_dir, "test_results.md")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Test Results\n\n")
        f.write(f"**Run summary:** {pass_count} passed, {fail_count} failed out of {len(TEST_CASES)} total\n\n")
        f.write("| # | Question | Expected Type | Actual Type | Pass/Fail |\n")
        f.write("|---|---|---|---|---|\n")
        for r in results_rows:
            icon = "PASS" if r["pass_fail"] == "PASS" else "FAIL"
            f.write(f"| {r['num']} | {r['question']} | {r['expected']} | {r['actual']} | {icon} |\n")

    print(f"\n  Results written to: {output_path}")


if __name__ == "__main__":
    main()
