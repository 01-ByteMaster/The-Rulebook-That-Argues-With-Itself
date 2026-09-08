"""
Configuration constants for the Rulebook QA system.
Thresholds are tuned empirically against corpus TF-IDF scores.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Retrieval ---
TOP_K = 10  # Number of top chunks returned by retrieval
CORPUS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "corpus")

# --- Classification Thresholds ---
# Tuned empirically against actual corpus TF-IDF scores (see tune_thresholds.py output).
#
# Score distribution observed (after corpus enrichment):
#   Not-covered questions: min=0.058, max=0.128, mean=0.085
#   Conflict questions:    min=0.126, max=0.145
#   Answered questions:    min=0.084, max=0.308, mean=0.198
#
# NOT_COVERED_THRESHOLD: if top-1 score < this, classify as not_covered.
# Set to 0.13 — clean separation between not-covered max (0.128) and conflict min (0.126).
NOT_COVERED_THRESHOLD = 0.13

# RELEVANCE_FLOOR: minimum score for a chunk to participate in conflict grouping.
# Set to 0.06 — low enough that FEE-5-REFUND-B (now scores ~0.07+ for hostel refund
# question after corpus enrichment) is included alongside HOSTEL-4-REFUND-A,
# but high enough to avoid false conflict triggers from generic term matches.
RELEVANCE_FLOOR = 0.06


# --- Optional Gemini LLM Layer ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_TIMEOUT = 5  # seconds
USE_GEMINI = bool(GEMINI_API_KEY)