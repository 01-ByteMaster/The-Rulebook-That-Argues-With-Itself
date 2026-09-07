# Rulebook QA System — Ridgeview University

> **"The Rulebook That Argues With Itself"** — A contradiction-aware QA system that ingests university policy documents, detects planted contradictions, and classifies questions as `answered`, `not_covered`, or `conflict`.

---

## Quick Start

### Prerequisites
- **Python 3.10+** installed and on PATH
- **pip** package manager

### Setup & Run

```bash
# 1. Navigate to the project
cd rulebook-qa

# 2. (Optional) Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Configure Gemini API for AI-enhanced answers
#    Copy .env.example to .env and add your API key from https://aistudio.google.com/
copy .env.example .env
#    Then edit .env and add your GEMINI_API_KEY
#    If not set, the system uses extractive answers (no LLM needed)

# 5. Start the server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 6. Open in browser
#    http://localhost:8000
```

The server starts, loads 40 corpus chunks from 5 documents, builds a TF-IDF index, and serves the frontend.

---

## Architecture

```
User Question
      │
      ▼
  ┌───────────┐
  │  Frontend  │  (Single HTML + vanilla JS)
  │ index.html │
  └─────┬─────┘
        │ POST /ask
        ▼
  ┌───────────┐     ┌───────────┐
  │  main.py   │────▶│ ingest.py │  (Loads corpus at startup)
  │  FastAPI   │     └───────────┘
  └─────┬─────┘
        │
        ▼
  ┌─────────────┐
  │ retrieval.py │  TF-IDF + cosine similarity → top-k chunks
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ classify.py  │  conflict → not_covered → answered (priority order)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ generate.py  │  Extractive answer (+ optional Gemini grounded phrasing)
  └─────────────┘
```

### Classification Priority (Spec Section 5)

1. **CONFLICT** — If ≥2 chunks from the same `conflict_group` score above `RELEVANCE_FLOOR`
2. **NOT_COVERED** — If best chunk score < `NOT_COVERED_THRESHOLD`
3. **ANSWERED** — Default fallback (topic is covered, no conflict)

---

## Corpus (5 Files, 40 Sections, ~7000+ Words)

| File | Format | Sections | Topics |
|------|--------|----------|--------|
| `01_attendance_policy.md` | Markdown | ATT-1 to ATT-9 | Attendance rules, 75% threshold, medical exemption, appeals |
| `02_hostel_handbook.md` | Markdown | HOSTEL-1 to HOSTEL-9 | Hostel rules, curfew, guest policy, deposit refund |
| `03_scholarship_policy.md` | Markdown | SCH-1 to SCH-8 | Scholarship eligibility, GPA requirements, renewals |
| `exam_regulations_SOURCE.md` | Markdown (PDF source) | EXAM-1 to EXAM-8 | Exam conduct, malpractice, committee waiver |
| `fee_deadlines_table.md` | Markdown (tables) | FEE-1 to FEE-6 | Fee deadlines, late fees, refund processing |

---

## 3 Planted Contradictions

### 1. `CG-ATTENDANCE` (3-way conflict)
- **ATT-2**: 75% attendance required
- **ATT-5-MEDICAL**: 60% with medical certificate
- **EXAM-7-COMMITTEE**: Committee can waive entirely
- **Test**: *"What is the minimum attendance percentage I need to sit my exam?"*

### 2. `CG-HOSTEL-REFUND` (2-way conflict)
- **HOSTEL-4-REFUND-A**: Refund within 15 working days
- **FEE-5-REFUND-B**: No refunds after 10th of the month
- **Test**: *"If I leave the hostel early, when do I get my deposit back?"*

### 3. `CG-SCHOLARSHIP-RENEWAL` (2-way conflict)
- **SCH-4-GPA-A**: CGPA ≥ 6.5 annually
- **SCH-6-GPA-B**: CGPA ≥ 7.0 every semester
- **Test**: *"What GPA do I need to keep my scholarship?"*

---

## API Contract

### `POST /ask`

**Request:**
```json
{ "question": "What is the hostel curfew time?" }
```

**Response:**
```json
{
  "type": "answered",
  "answer": "Per Section HOSTEL-2: ...",
  "passages": [
    {
      "section_id": "HOSTEL-2",
      "source_file": "02_hostel_handbook.md",
      "text": "...",
      "score": 0.1505
    }
  ],
  "conflict_note": null
}
```

Response `type` is one of: `answered` | `not_covered` | `conflict`

### `GET /health`
Returns system status and chunk count.

---

## Testing

### Run Full Test Suite (35 questions)
```bash
python -m backend.run_tests
```

This runs 25 not-covered + 3 conflict + 7 answered questions and writes results to `data/test_results.md`.

### Run Threshold Tuning
```bash
python -m backend.tune_thresholds
```

Shows score distributions for each question category and recommends threshold values.

### Test Results Summary
All 35 test cases pass:
- ✅ 25/25 not_covered questions correctly classified
- ✅ 3/3 conflict questions correctly detected with proper passages
- ✅ 7/7 answered questions correctly classified with relevant answers

---

## Frontend

The frontend is a single-page dark-themed UI at `http://localhost:8000/` featuring:
- Search bar with quick-question shortcuts
- Color-coded badges: 🟢 ANSWERED, ⚫ NOT COVERED, 🔴 CONFLICT
- Passage cards with section ID, source file, similarity score
- Conflict passages displayed with "VS" separators
- Expandable passage text with smooth animations

---

## Configuration

All thresholds are in `backend/config.py`:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `NOT_COVERED_THRESHOLD` | 0.13 | Below this top-1 score → not_covered |
| `RELEVANCE_FLOOR` | 0.06 | Minimum score for conflict group membership |
| `TOP_K` | 10 | Number of chunks retrieved per query |
| `GEMINI_API_KEY` | (env) | Optional; enables AI-phrased answers |

---

## Project Structure

```
rulebook-qa/
├── corpus/                          # Policy documents (5 files)
│   ├── 01_attendance_policy.md
│   ├── 02_hostel_handbook.md
│   ├── 03_scholarship_policy.md
│   ├── exam_regulations_SOURCE.md
│   └── fee_deadlines_table.md
├── data/                            # Test artifacts
│   ├── contradictions.md            # Contradiction tracking doc
│   ├── not_covered_questions.md     # 25 not-covered questions
│   └── test_results.md              # Test execution results
├── backend/                         # FastAPI application
│   ├── main.py                      # App entry point, /ask endpoint
│   ├── ingest.py                    # Corpus loading + section parsing
│   ├── retrieval.py                 # TF-IDF index + cosine search
│   ├── classify.py                  # conflict → not_covered → answered
│   ├── generate.py                  # Extractive + optional Gemini answers
│   ├── models.py                    # Pydantic v2 schemas
│   ├── config.py                    # Thresholds + configuration
│   ├── run_tests.py                 # Full test suite
│   └── tune_thresholds.py           # Threshold tuning utility
├── frontend/
│   └── index.html                   # Single-page UI
├── .env.example                     # Environment variable template
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```
