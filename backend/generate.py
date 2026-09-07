"""
Answer generation module.
Extractive by default; optional Gemini-based grounded phrasing layer.
"""

import traceback
from backend.retrieval import RetrievalResult
from backend.config import USE_GEMINI, GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TIMEOUT


def _extractive_answer(question: str, passages: list[RetrievalResult]) -> str:
    """
    Generate an extractive answer from the top passages.
    Simply returns the top passage text with section citation.
    """
    if not passages:
        return "No relevant information found in the corpus."

    top = passages[0]
    # Clean up the text for presentation — remove heading markers
    text = top.text.strip()
    # Remove markdown heading prefix if present
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('## '):
            continue  # Skip the heading line, section_id already identifies it
        if stripped:
            cleaned_lines.append(stripped)

    answer_text = ' '.join(cleaned_lines[:5])  # First few lines as answer

    # Truncate to reasonable length
    if len(answer_text) > 800:
        answer_text = answer_text[:800].rsplit(' ', 1)[0] + "..."

    return f"Per Section {top.section_id}: {answer_text}"


def _gemini_answer(question: str, passages: list[RetrievalResult]) -> str:
    """
    Use Gemini API for grounded answer generation.
    Strictly grounded — LLM must only use provided passages.
    Falls back to extractive on any failure.
    """
    try:
        import google.generativeai as genai
        import signal

        genai.configure(api_key=GEMINI_API_KEY)

        # Build passages text
        passages_text = ""
        for p in passages[:5]:  # Limit to top 5 passages
            clean_text = p.text.replace('## ', '').strip()
            passages_text += f"{clean_text} [Section {p.section_id}]\n\n"

        prompt = (
            "Answer the question using ONLY the passages below. Do not use outside knowledge.\n"
            "If the passages do not fully support an answer, say so plainly.\n\n"
            f"Question: {question}\n\n"
            f"Passages:\n{passages_text}\n"
            "Answer:"
        )

        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=300,
                temperature=0.1
            ),
            request_options={"timeout": GEMINI_TIMEOUT}
        )

        if response and response.text:
            return response.text.strip()
        else:
            raise ValueError("Empty Gemini response")

    except Exception as e:
        print(f"[generate] Gemini call failed, falling back to extractive: {e}")
        traceback.print_exc()
        return _extractive_answer(question, passages)


def generate_answer(question: str, passages: list[RetrievalResult]) -> str:
    """
    Generate an answer for an 'answered' type response.
    Uses Gemini if available and configured, otherwise extractive.
    """
    if not passages:
        return "No relevant information found in the corpus."

    if USE_GEMINI:
        return _gemini_answer(question, passages)
    else:
        return _extractive_answer(question, passages)
