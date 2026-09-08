# Rulebook QA System — Medicaps University

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

![System Architecture](rulebook-qa\system-architecture-rulebook-qa.excalidraw.svg)

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

### Full Test Suite

Run the complete test suite containing **35 test cases**:

```bash
python -m backend.run_tests
```

The test results are saved to:

```text
data/test_results.md
```

### Test Coverage

| Category    | Test Cases |       Result       |
| :---------- | ---------: | :----------------: |
| Not Covered |         25 |   ✅ 25/25 Passed   |
| Conflict    |          3 |   ✅ 3/3 Detected   |
| Answered    |          7 |    ✅ 7/7 Passed    |
| **Total**   |     **35** | **✅ 35/35 Passed** |

### Threshold Tuning

To analyze similarity-score distributions and determine suitable classification thresholds:

```bash
python -m backend.tune_thresholds
```

This analyzes the scores for each question category and provides recommended threshold values.

### Test Result

All **35 test cases passed successfully**, validating:

* Correct classification of covered and not-covered queries
* Accurate detection of conflicting rules
* Retrieval of relevant supporting passages
* Appropriate similarity-based classification

---

## Frontend

The project includes a **single-page, dark-themed web interface** accessible at:

```text
http://localhost:8000/
```

### Key Features

| Feature                   | Description                                                      |
| :------------------------ | :--------------------------------------------------------------- |
| **Search Interface**      | Search bar with quick-question shortcuts                         |
| **Result Classification** | Color-coded badges for `ANSWERED`, `NOT COVERED`, and `CONFLICT` |
| **Passage Cards**         | Displays section ID, source file, and similarity score           |
| **Conflict View**         | Shows conflicting passages with a clear **VS** separator         |
| **Expandable Passages**   | Allows users to expand or collapse passage text                  |

The frontend provides a **simple and intuitive view of search results, supporting evidence, and detected rule conflicts**.


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
