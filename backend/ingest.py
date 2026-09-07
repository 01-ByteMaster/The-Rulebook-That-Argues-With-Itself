"""
Corpus ingestion module.
Loads markdown files and PDF, parses section_id / conflict_group metadata from HTML comments,
and produces a list of Chunk objects for the retrieval index.
"""

import os
import re
import glob
from dataclasses import dataclass
from typing import Optional


@dataclass
class Chunk:
    """A single section from the corpus with metadata."""
    section_id: str
    source_file: str
    text: str
    conflict_group: Optional[str] = None


# Regex to match section metadata in HTML comments:
# <!-- section_id: ATT-2 | conflict_group: CG-ATTENDANCE -->
METADATA_PATTERN = re.compile(
    r'<!--\s*section_id:\s*(?P<section_id>[^\s|]+)\s*\|\s*conflict_group:\s*(?P<conflict_group>\S+)\s*-->',
    re.IGNORECASE
)

# Regex to split markdown by level-2 headings
SECTION_SPLIT_PATTERN = re.compile(r'^##\s+', re.MULTILINE)


def _parse_markdown(filepath: str) -> list[Chunk]:
    """Parse a markdown file into Chunk objects, one per ## section."""
    filename = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    chunks = []

    # Split on ## headings, keeping the heading with each section
    parts = re.split(r'(^## .+$)', content, flags=re.MULTILINE)

    # parts alternates: [preamble, heading1, body1, heading2, body2, ...]
    # Process pairs of (heading, body)
    i = 1  # skip preamble (index 0)
    while i < len(parts):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        full_section = heading + "\n" + body

        # Try to extract metadata from the HTML comment
        match = METADATA_PATTERN.search(full_section)
        if match:
            section_id = match.group('section_id')
            conflict_group_raw = match.group('conflict_group')
            conflict_group = None if conflict_group_raw.lower() == 'null' else conflict_group_raw

            # Remove the metadata comment from the text for cleaner retrieval
            clean_text = METADATA_PATTERN.sub('', full_section).strip()

            chunks.append(Chunk(
                section_id=section_id,
                source_file=filename,
                text=clean_text,
                conflict_group=conflict_group
            ))
        else:
            # Section without metadata — skip (could be preamble or title)
            pass

        i += 2

    return chunks


def _parse_pdf(filepath: str) -> list[Chunk]:
    """
    Parse a PDF file into Chunk objects.
    Falls back to reading the markdown source if PDF parsing fails.
    """
    filename = os.path.basename(filepath)

    try:
        import pypdf
        reader = pypdf.PdfReader(filepath)
        full_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

        if not full_text.strip():
            raise ValueError("Empty PDF text extraction")

    except Exception:
        # Fallback: try to find the markdown source alongside the PDF
        md_source = filepath.replace('.pdf', '_SOURCE.md')
        if not os.path.exists(md_source):
            md_source = filepath.replace('.pdf', '.md')
        if os.path.exists(md_source):
            return _parse_markdown(md_source)
        return []

    # Parse sections from extracted PDF text
    # PDF text extraction loses markdown formatting, so we look for section headers
    # that match pattern like "EXAM-1:" or "## EXAM-1:"
    chunks = []
    # Try to split by section headers in the extracted text
    section_pattern = re.compile(r'(?:^|\n)((?:## )?(?:EXAM-\d+[\w-]*)[:\s])', re.MULTILINE)
    parts = section_pattern.split(full_text)

    if len(parts) <= 1:
        # PDF text doesn't have recognizable section structure
        # Fall back to markdown source
        md_source = filepath.replace('.pdf', '_SOURCE.md')
        if not os.path.exists(md_source):
            md_source = filepath.replace('.pdf', '.md')
        if os.path.exists(md_source):
            return _parse_markdown(md_source)
        # Last resort: treat entire PDF as one chunk
        return [Chunk(
            section_id="EXAM-FULL",
            source_file=filename,
            text=full_text.strip(),
            conflict_group=None
        )]

    # Process pairs
    i = 1
    while i < len(parts):
        header = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        section_text = header + " " + body

        section_id_match = re.match(r'(?:## )?(EXAM-[\w-]+)', header)
        section_id = section_id_match.group(1) if section_id_match else f"EXAM-UNK-{i}"

        # Determine conflict group from known mapping
        conflict_group = None
        if section_id == "EXAM-7-COMMITTEE":
            conflict_group = "CG-ATTENDANCE"

        chunks.append(Chunk(
            section_id=section_id,
            source_file=filename,
            text=section_text,
            conflict_group=conflict_group
        ))
        i += 2

    return chunks


def load_corpus(corpus_dir: str) -> list[Chunk]:
    """
    Load all corpus files from the given directory.
    Supports .md (markdown) and .pdf files.
    Returns a list of Chunk objects.
    """
    all_chunks = []

    # Load markdown files
    md_files = sorted(glob.glob(os.path.join(corpus_dir, "*.md")))
    for md_file in md_files:
        basename = os.path.basename(md_file)
        # Skip the SOURCE markdown if a PDF version exists
        if basename.endswith("_SOURCE.md"):
            pdf_equivalent = md_file.replace("_SOURCE.md", ".pdf")
            if os.path.exists(pdf_equivalent):
                continue  # Will be loaded via PDF path
        chunks = _parse_markdown(md_file)
        all_chunks.extend(chunks)

    # Load PDF files
    pdf_files = sorted(glob.glob(os.path.join(corpus_dir, "*.pdf")))
    for pdf_file in pdf_files:
        chunks = _parse_pdf(pdf_file)
        all_chunks.extend(chunks)

    # If no PDF was found but the SOURCE markdown exists, load it directly
    exam_source = os.path.join(corpus_dir, "exam_regulations_SOURCE.md")
    exam_pdf = os.path.join(corpus_dir, "exam_regulations.pdf")
    if os.path.exists(exam_source) and not os.path.exists(exam_pdf):
        # Check if we already loaded it (it shouldn't have been skipped if no PDF)
        existing_ids = {c.section_id for c in all_chunks}
        if "EXAM-7-COMMITTEE" not in existing_ids:
            chunks = _parse_markdown(exam_source)
            all_chunks.extend(chunks)

    print(f"[ingest] Loaded {len(all_chunks)} chunks from {corpus_dir}")
    for chunk in all_chunks:
        cg = chunk.conflict_group or "null"
        print(f"  - {chunk.section_id} ({chunk.source_file}) [conflict_group: {cg}] — {len(chunk.text)} chars")

    return all_chunks
