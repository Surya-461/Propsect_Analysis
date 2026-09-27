"""
Proposal Service for Proposal-Based Prospect Analysis.
Handles PDF/DOCX validation, structural text extraction, section identification,
and structured Proposal Profile synthesis.
"""

import io
import os
import re
import uuid
import logging
from typing import Dict, Any, List, Optional
import pypdf

from ai.gemini import query_gemini
from ai.ollama import query_ollama, PRIMARY_OLLAMA_MODEL
from services.proposal_retrieval_service import create_canonical_chunks

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
MAX_PDF_SIZE_BYTES = MAX_FILE_SIZE_BYTES
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def validate_pdf(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Validates document file format (PDF, DOCX, TXT), file size, and extractable readability.
    Returns validation dictionary with status and metadata.
    """
    return validate_document(file_bytes, filename)


def validate_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Validates document file format (PDF, DOCX, TXT), file size, and extractable readability.
    Returns validation dictionary with status and metadata.
    """
    if not filename:
        return {
            "valid": False,
            "error": "Unable to process this file. Please upload a valid PDF or DOCX proposal/RFP.",
            "filename": "unknown",
            "file_size": len(file_bytes) if file_bytes else 0,
            "page_count": 0
        }

    ext = os.path.splitext(filename.lower())[1]
    if ext == ".doc":
        return {
            "valid": False,
            "error": "Legacy binary .doc format is not supported. Please save and upload as .docx or .pdf.",
            "filename": filename,
            "file_size": len(file_bytes) if file_bytes else 0,
            "page_count": 0
        }

    if ext not in ALLOWED_EXTENSIONS:
        return {
            "valid": False,
            "error": "Unable to process this file. Please upload a valid PDF or DOCX proposal/RFP.",
            "filename": filename,
            "file_size": len(file_bytes) if file_bytes else 0,
            "page_count": 0
        }

    if not file_bytes or len(file_bytes) == 0:
        return {
            "valid": False,
            "error": "The uploaded proposal file is empty.",
            "filename": filename,
            "file_size": 0,
            "page_count": 0
        }

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return {
            "valid": False,
            "error": f"File size exceeds the 15 MB limit ({len(file_bytes) / (1024*1024):.1f} MB uploaded).",
            "filename": filename,
            "file_size": len(file_bytes),
            "page_count": 0
        }

    try:
        if ext == ".pdf":
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            num_pages = len(reader.pages)
            if num_pages == 0:
                return {
                    "valid": False,
                    "error": "The uploaded PDF document contains 0 pages.",
                    "filename": filename,
                    "file_size": len(file_bytes),
                    "page_count": 0
                }

            # Check for readable content across pages
            full_sample = ""
            for page in reader.pages[:5]:
                p_text = page.extract_text() or ""
                full_sample += p_text.strip()
                if len(full_sample) >= 40:
                    break

            if len(full_sample.strip()) < 20:
                return {
                    "valid": False,
                    "error": "The uploaded proposal does not contain sufficient readable content for analysis.",
                    "filename": filename,
                    "file_size": len(file_bytes),
                    "page_count": num_pages
                }

            return {
                "valid": True,
                "error": None,
                "filename": filename,
                "file_size": len(file_bytes),
                "page_count": num_pages
            }

        elif ext == ".docx":
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            lines = []
            for p in doc.paragraphs:
                if p.text and p.text.strip():
                    lines.append(p.text.strip())
            for t in doc.tables:
                for row in t.rows:
                    row_cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if row_cells:
                        lines.append(" | ".join(row_cells))
            full_text = "\n".join(lines).strip()
            if len(full_text) < 20:
                return {
                    "valid": False,
                    "error": "The uploaded proposal does not contain sufficient readable content for analysis.",
                    "filename": filename,
                    "file_size": len(file_bytes),
                    "page_count": 0
                }
            est_pages = max(1, (len(full_text) // 2500) + 1)
            return {
                "valid": True,
                "error": None,
                "filename": filename,
                "file_size": len(file_bytes),
                "page_count": est_pages
            }

        elif ext == ".txt":
            raw_text = file_bytes.decode("utf-8", errors="ignore").strip()
            if len(raw_text) < 20:
                return {
                    "valid": False,
                    "error": "The uploaded proposal does not contain sufficient readable content for analysis.",
                    "filename": filename,
                    "file_size": len(file_bytes),
                    "page_count": 0
                }
            est_pages = max(1, (len(raw_text) // 2500) + 1)
            return {
                "valid": True,
                "error": None,
                "filename": filename,
                "file_size": len(file_bytes),
                "page_count": est_pages
            }

        return {
            "valid": False,
            "error": "Unable to process this file. Please upload a valid PDF or DOCX proposal/RFP.",
            "filename": filename,
            "file_size": len(file_bytes),
            "page_count": 0
        }

    except Exception as e:
        logger.error("Document validation failure for %s: %s", filename, e)
        return {
            "valid": False,
            "error": "Unable to process this file. Please upload a valid PDF or DOCX proposal/RFP.",
            "filename": filename,
            "file_size": len(file_bytes),
            "page_count": 0
        }


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extracts text from PDF, DOCX, DOC, or TXT file while preserving paragraph and table structure.
    Employs pdfplumber with table extraction and page markers when available, falling back to pypdf.
    """
    if not file_bytes:
        return ""
    ext = os.path.splitext((filename or "").lower())[1]

    if ext == ".pdf":
        # 1. Attempt pdfplumber for layout & table preservation
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                extracted_pages = []
                for idx, page in enumerate(pdf.pages):
                    page_text = page.extract_text(layout=False) or page.extract_text() or ""
                    clean_page = re.sub(r'[ \t]+', ' ', page_text).strip()
                    
                    # Extract tables as structured pipe-delimited text
                    tables = page.extract_tables() or []
                    table_lines = []
                    for t in tables:
                        for row in t:
                            cells = [str(c or "").strip().replace("\n", " ") for c in row if c is not None]
                            if any(cells):
                                table_lines.append(" | ".join(cells))
                    
                    full_page_str = clean_page
                    if table_lines:
                        full_page_str += "\n\n" + "\n".join(table_lines)
                    
                    if full_page_str.strip():
                        extracted_pages.append(f"--- Page {idx + 1} ---\n{full_page_str.strip()}")
                if extracted_pages:
                    return "\n\n".join(extracted_pages)
        except Exception as e:
            logger.warning("pdfplumber extraction skipped/failed: %s; falling back to pypdf", e)

        # 2. Fallback to pypdf
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            extracted_pages = []
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    clean_page = re.sub(r'[ \t]+', ' ', page_text)
                    extracted_pages.append(f"--- Page {idx + 1} ---\n{clean_page.strip()}")
            return "\n\n".join(extracted_pages)
        except Exception as e:
            logger.error("Failed to extract text from PDF %s: %s", filename, e)
            return ""

    elif ext == ".docx":
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            lines = []
            for p in doc.paragraphs:
                if p.text and p.text.strip():
                    clean_p = re.sub(r'[ \t]+', ' ', p.text).strip()
                    lines.append(clean_p)
            for t in doc.tables:
                for row in t.rows:
                    row_cells = [re.sub(r'[ \t]+', ' ', c.text).strip() for c in row.cells if c.text.strip()]
                    if row_cells:
                        lines.append(" | ".join(row_cells))
            return "\n\n".join(lines)
        except Exception as e:
            logger.error("Failed to extract text from DOCX %s: %s", filename, e)
            return ""

    elif ext == ".txt":
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error("Failed to decode TXT file %s: %s", filename, e)
            return ""

    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""


SECTION_PATTERNS = {
    "overview": r'(?i)(?:^|\n)\s*(?:1[\.\s]+|section\s+1\b|overview|executive\s+summary|introduction|background|about\s+this\s+(?:rfp|proposal)|context)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[2-9]|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)',
    "objectives": r'(?i)(?:^|\n)\s*(?:[0-9]+[\.\s]+|section\b\s*[0-9]*|business\s+)?(?:objectives?|goals?|purpose|business\s+drivers?|expected\s+outcomes?|strategic\s+goals?)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[0-9]+|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)',
    "business_problems": r'(?i)(?:^|\n)\s*(?:[0-9]+[\.\s]+|section\b\s*[0-9]*|business\s+)?(?:challenges?|pain\s*points?|problems?|deficienc(?:y|ies)|bottlenecks?|operational\s+gaps?)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[0-9]+|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)',
    "functional_requirements": r'(?i)(?:^|\n)\s*(?:[0-9]+[\.\s]+|section\b\s*[0-9]*|scope\s+of\s+work|functional\s+requirements?|key\s+deliverables?|core\s+features?|underwriting\s+requirements?|claims\s+specifications?|statement\s+of\s+work|specifications?)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[0-9]+|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)',
    "technical_requirements": r'(?i)(?:^|\n)\s*(?:[0-9]+[\.\s]+|section\b\s*[0-9]*|technical\s+)?(?:architecture|technical\s+specifications?|technology\s+stack|cloud\s+requirements?|platform\s+specifications?|infrastructure|system\s+requirements?)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[0-9]+|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)',
    "ai_ml_requirements": r'(?i)(?:^|\n)\s*(?:[0-9]+[\.\s]+|section\b\s*[0-9]*|ai\s*/\s*ml|artificial\s+intelligence|machine\s+learning|predictive\s+modeling|cognitive\s+intake|cognitive\s+underwriting)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[0-9]+|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)',
    "data_requirements": r'(?i)(?:^|\n)\s*(?:[0-9]+[\.\s]+|section\b\s*[0-9]*|data\s+)?(?:data\s+requirements?|data\s+lake|data\s+analytics?|data\s+ingestion|reporting\s+requirements?|data\s+model|telemetry)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[0-9]+|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)',
    "integration_requirements": r'(?i)(?:^|\n)\s*(?:[0-9]+[\.\s]+|section\b\s*[0-9]*|integration\s+)?(?:integrations?|api\s+specifications?|core\s+systems?|interfaces?|connectors?)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[0-9]+|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)',
    "security_regulatory": r'(?i)(?:^|\n)\s*(?:[0-9]+[\.\s]+|section\b\s*[0-9]*|security\s+)?(?:security|compliance|regulatory|statutory|soc\s*2|iso\s*27001|gdpr|dpdp|data\s+privacy|infosec|governance)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[0-9]+|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)',
    "evaluation_criteria": r'(?i)(?:^|\n)\s*(?:[0-9]+[\.\s]+|section\b\s*[0-9]*|evaluation\s+)?(?:evaluation\s+criteria|selection\s+criteria|vendor\s+qualifications?|scoring\s+methodology|evaluation\s+weights?|award\s+criteria)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[0-9]+|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)',
    "commercial_terms": r'(?i)(?:^|\n)\s*(?:[0-9]+[\.\s]+|section\b\s*[0-9]*|commercial\s+)?(?:commercial\s+terms|pricing|budget|payment\s+terms|fee\s+structure|commercial\s+proposal)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[0-9]+|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)',
    "timeline": r'(?i)(?:^|\n)\s*(?:[0-9]+[\.\s]+|section\b\s*[0-9]*|project\s+)?(?:timeline|schedule|milestones?|deadlines?|key\s+dates|delivery\s+phases?|go\-live)\b[^\n]*\n(.*?)(?=\n\s*(?:(?:[0-9]+|\d{2})[\.\s]+|section\b|[A-Z\s]{4,35}[:\-])|\Z)'
}


def chunk_document_hierarchically(
    text: str,
    chunk_size: int = 3500,
    overlap: int = 400
) -> List[Dict[str, Any]]:
    """
    Splits document text hierarchically into sliding window chunks with overlap,
    respecting paragraph and sentence boundaries.
    """
    if not text:
        return []

    clean_text = text.strip()
    if len(clean_text) <= chunk_size:
        return [{
            "chunk_index": 0,
            "text": clean_text,
            "start_char": 0,
            "end_char": len(clean_text)
        }]

    # Split into structural paragraphs
    paragraphs = re.split(r'\n{2,}', clean_text)
    chunks: List[Dict[str, Any]] = []
    current_chunk = ""
    start_pos = 0

    for para in paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue

        if len(current_chunk) + len(para_clean) + 2 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{para_clean}".strip()
        else:
            if current_chunk:
                chunks.append({
                    "chunk_index": len(chunks),
                    "text": current_chunk,
                    "start_char": start_pos,
                    "end_char": start_pos + len(current_chunk)
                })
                # Preserve overlap from tail of current chunk
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                start_pos += max(1, len(current_chunk) - len(overlap_text))
                current_chunk = f"{overlap_text}\n\n{para_clean}".strip()
            else:
                # Individual paragraph exceeds chunk_size, split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para_clean)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                        current_chunk = f"{current_chunk} {sentence}".strip()
                    else:
                        if current_chunk:
                            chunks.append({
                                "chunk_index": len(chunks),
                                "text": current_chunk,
                                "start_char": start_pos,
                                "end_char": start_pos + len(current_chunk)
                            })
                            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                            start_pos += max(1, len(current_chunk) - len(overlap_text))
                            current_chunk = f"{overlap_text} {sentence}".strip()
                        else:
                            # Hard split very long single token sentence
                            chunks.append({
                                "chunk_index": len(chunks),
                                "text": sentence[:chunk_size],
                                "start_char": start_pos,
                                "end_char": start_pos + chunk_size
                            })
                            start_pos += chunk_size
                            current_chunk = sentence[chunk_size - overlap:]

    if current_chunk:
        chunks.append({
            "chunk_index": len(chunks),
            "text": current_chunk,
            "start_char": start_pos,
            "end_char": start_pos + len(current_chunk)
        })

    return chunks


def classify_and_aggregate_sections(text: str) -> Dict[str, str]:
    """
    Identifies and aggregates RFP / Proposal sections across the entire document text
    using both regex pattern boundaries and hierarchical chunk classifications.
    """
    sections: Dict[str, str] = {
        "overview": "",
        "objectives": "",
        "business_problems": "",
        "functional_requirements": "",
        "technical_requirements": "",
        "ai_ml_requirements": "",
        "data_requirements": "",
        "integration_requirements": "",
        "security_regulatory": "",
        "evaluation_criteria": "",
        "commercial_terms": "",
        "timeline": ""
    }

    if not text:
        return sections

    # 1. Direct Regex Pattern Matching across full document
    for key, pat in SECTION_PATTERNS.items():
        matches = re.finditer(pat, text, re.DOTALL)
        matched_chunks = []
        for m in matches:
            content = m.group(1).strip()
            if content and len(content) >= 30:
                matched_chunks.append(content[:4000])
        if matched_chunks:
            sections[key] = "\n\n".join(matched_chunks)[:6000]

    # 2. Hierarchical Chunk Tagging Fallback (catches sections without numbered headers)
    chunks = chunk_document_hierarchically(text, chunk_size=3500, overlap=400)
    chunk_tag_map = {
        "objectives": ["objective", "goal", "purpose", "driver", "target"],
        "business_problems": ["problem", "challenge", "pain point", "bottleneck", "deficiency"],
        "functional_requirements": ["functional requirement", "scope of work", "deliverable", "specification", "underwriting requirement", "claims requirement"],
        "technical_requirements": ["architecture", "technology stack", "cloud", "infrastructure", "microservice", "devops"],
        "ai_ml_requirements": ["ai/ml", "machine learning", "artificial intelligence", "predictive", "cognitive", "nlp", "llm"],
        "data_requirements": ["data lake", "data pipeline", "analytics", "reporting", "warehouse", "telemetry"],
        "integration_requirements": ["api", "integration", "connector", "interface", "core system", "web service", "rest"],
        "security_regulatory": ["security", "compliance", "regulatory", "soc 2", "iso 27001", "gdpr", "dpdp", "encryption", "privacy"],
        "evaluation_criteria": ["evaluation", "selection criteria", "scoring", "weight", "qualification", "vendor requirement"],
        "commercial_terms": ["pricing", "cost", "budget", "commercial", "fixed price", "payment schedule", "fee"],
        "timeline": ["timeline", "milestone", "deadline", "go-live", "rollout schedule", "duration", "phase 1", "phase 2"]
    }

    for chunk in chunks:
        c_text = chunk["text"]
        c_lower = c_text.lower()
        for sec_key, keywords in chunk_tag_map.items():
            if not sections.get(sec_key) or len(sections[sec_key]) < 200:
                # Count keyword hits in this chunk
                matches_count = sum(1 for kw in keywords if kw in c_lower)
                if matches_count >= 2:
                    existing = sections.get(sec_key, "")
                    if existing:
                        sections[sec_key] = f"{existing}\n\n{c_text}"[:6000]
                    else:
                        sections[sec_key] = c_text[:4000]

    # Overview defaults to the top 2000 characters if not explicitly captured
    if not sections.get("overview") or len(sections["overview"]) < 100:
        sections["overview"] = text[:2000].strip()

    return sections


def extract_sections(text: str) -> Dict[str, str]:
    """
    Identifies common RFP / Proposal sections from extracted text.
    Backward-compatible entry point returning standard section dictionary.
    """
    agg = classify_and_aggregate_sections(text)
    return {
        "overview": agg.get("overview", "")[:2500],
        "objectives": agg.get("objectives", "")[:2500],
        "requirements": agg.get("functional_requirements", "")[:3500],
        "capabilities": f"{agg.get('technical_requirements', '')}\n{agg.get('ai_ml_requirements', '')}".strip()[:3000],
        "evaluation_criteria": agg.get("evaluation_criteria", "")[:2500],
        "commercial_terms": agg.get("commercial_terms", "")[:2500]
    }


def build_aggregated_proposal_context(text: str, max_context_chars: int = 24000) -> str:
    """
    Compiles a comprehensive, high-density multi-section context digest spanning
    the entire RFP document from first page to last, eliminating naive character slicing.
    """
    if not text:
        return ""

    if len(text) <= 8000:
        return text

    sections = classify_and_aggregate_sections(text)
    digest_parts: List[str] = []

    # 1. Document Overview & Context
    overview_text = sections.get("overview", "").strip() or text[:2000].strip()
    digest_parts.append(f"### 1. DOCUMENT OVERVIEW & CONTEXT\n{overview_text[:2500]}")

    # 2. Objectives & Business Problems
    obj_text = sections.get("objectives", "").strip()
    prob_text = sections.get("business_problems", "").strip()
    if obj_text or prob_text:
        combined_obj = "\n".join(filter(None, [f"Objectives:\n{obj_text[:1800]}" if obj_text else "", f"Business Problems:\n{prob_text[:1500]}" if prob_text else ""]))
        digest_parts.append(f"### 2. BUSINESS OBJECTIVES & PROBLEMS\n{combined_obj}")

    # 3. Scope of Work & Functional Requirements
    func_text = sections.get("functional_requirements", "").strip()
    if func_text:
        digest_parts.append(f"### 3. SCOPE & FUNCTIONAL REQUIREMENTS\n{func_text[:4000]}")

    # 4. Technical Architecture, AI/ML & Data Requirements
    tech_parts = []
    if sections.get("technical_requirements"):
        tech_parts.append(f"Technical Architecture:\n{sections['technical_requirements'][:2000]}")
    if sections.get("ai_ml_requirements"):
        tech_parts.append(f"AI/ML Requirements:\n{sections['ai_ml_requirements'][:1500]}")
    if sections.get("data_requirements"):
        tech_parts.append(f"Data & Analytics:\n{sections['data_requirements'][:1500]}")
    if sections.get("integration_requirements"):
        tech_parts.append(f"System Integration:\n{sections['integration_requirements'][:1500]}")
    if tech_parts:
        digest_parts.append(f"### 4. TECHNICAL, AI/ML & INTEGRATION SPECIFICATIONS\n" + "\n\n".join(tech_parts))

    # 5. Security, Privacy & Regulatory Compliance
    sec_text = sections.get("security_regulatory", "").strip()
    if sec_text:
        digest_parts.append(f"### 5. SECURITY, REGULATORY & COMPLIANCE\n{sec_text[:2500]}")

    # 6. Evaluation Criteria & Commercial Terms
    eval_text = sections.get("evaluation_criteria", "").strip()
    comm_text = sections.get("commercial_terms", "").strip()
    if eval_text or comm_text:
        combined_eval = "\n\n".join(filter(None, [f"Evaluation Criteria:\n{eval_text[:2000]}" if eval_text else "", f"Commercial Terms:\n{comm_text[:1500]}" if comm_text else ""]))
        digest_parts.append(f"### 6. EVALUATION CRITERIA & COMMERCIAL TERMS\n{combined_eval}")

    # 7. Timeline & Implementation Roadmap
    time_text = sections.get("timeline", "").strip()
    if time_text:
        digest_parts.append(f"### 7. TIMELINE & IMPLEMENTATION ROADMAP\n{time_text[:2000]}")

    # 8. Concluding Summary & Final Requirement Statements (from document tail)
    doc_tail = text[-3000:].strip()
    digest_parts.append(f"### 8. DOCUMENT CLOSING & SUBMISSION SPECIFICATIONS\n{doc_tail}")

    aggregated_context = "\n\n".join(digest_parts)
    return aggregated_context[:max_context_chars]


def extract_requirements(text: str) -> List[str]:
    """
    Extracts actionable RFP / proposal requirements across the entire document text,
    including table rows, appendix line items, and SLA/penalty specifications.
    """
    if not text:
        return []

    requirements: List[str] = []
    
    # 1. Bullet items and numbered clauses
    bullet_items = re.findall(r'(?:^|\n)\s*(?:[\*\-•]|\d+[\.\)])\s*([A-Z0-9][^\n]{10,260})', text)
    for b in bullet_items:
        clean = b.strip()
        if any(k in clean.lower() for k in [
            "must", "shall", "require", "support", "provide", "integrate", "automate",
            "underwriting", "risk", "api", "ai", "platform", "cloud", "security", "sla",
            "data", "penalty", "turnaround", "settlement", "adjudication", "fnol", "soc 2",
            "iso", "gdpr", "dpdp", "portal", "loss ratio", "combined ratio", "audit"
        ]):
            requirements.append(clean)

    # 2. Table-delimited rows with specification/requirement data
    table_rows = re.findall(r'(?:^|\n)\s*([A-Za-z0-9\s/–-]{4,40})\s*\|\s*([^\n]{10,240})', text)
    for col1, col2 in table_rows:
        row_str = f"{col1.strip()}: {col2.strip()}"
        if any(k in row_str.lower() for k in [
            "sla", "turnaround", "requirement", "metric", "timeline", "scope", "specification",
            "mandatory", "standard", "compliance", "api", "security", "support", "target"
        ]):
            requirements.append(row_str)

    # 3. Fallback to key requirement statements
    for sentence in re.split(r'[\.\n]+', text):
        s = sentence.strip()
        if 25 <= len(s) <= 240 and any(k in s.lower() for k in [
            "underwriting", "risk scoring", "submission automation", "data integration",
            "workflow", "compliance", "portal", "cloud", "api", "claims settlement",
            "turnaround time", "penalty clause", "warranty", "audit requirement"
        ]):
            requirements.append(s)

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for r in requirements:
        low = r.lower()
        if low not in seen:
            seen.add(low)
            deduped.append(r)

    return deduped[:35]



def extract_objectives(text: str) -> List[str]:
    """
    Extracts core business objectives across the entire proposal text.
    """
    if not text:
        return []

    objectives: List[str] = []
    obj_matches = re.findall(r'(?i)(?:improve|enhance|automate|streamline|reduce|accelerate|enable|deliver|modernize|scale|provide|ensure|cover|manage)\s+([^\n\.,;]{10,140})', text)
    for verb_match in obj_matches:
        full_obj = verb_match.strip()
        if full_obj and len(full_obj) >= 15:
            objectives.append(full_obj.capitalize())

    seen = set()
    deduped = []
    for obj in objectives:
        low = obj.lower()
        if low not in seen:
            seen.add(low)
            deduped.append(obj)

    return deduped[:8]


def extract_capabilities(text: str) -> List[str]:
    """
    Identifies expected solution capabilities and technological competencies across document.
    """
    if not text:
        return []

    capability_keywords = [
        "AI/ML", "Machine Learning", "Underwriting Automation", "Underwriting", "Risk Scoring",
        "Commercial Risk Assessment", "Cyber Risk", "Cloud Security", "Portfolio Analytics",
        "API Integration", "Cloud Modernization", "Document Intelligence", "Claims Automation",
        "Claims Management", "Fraud Detection", "Regulatory Compliance", "Compliance",
        "Workflow Orchestration", "Telemetry & Data Ingestion", "Actuarial Modeling",
        "Reinsurance", "Life Insurance", "Commercial Insurance", "GenAI", "Real-Time Pricing"
    ]

    matched = []
    text_lower = text.lower()
    for cap in capability_keywords:
        if cap.lower() in text_lower:
            matched.append(cap)

    return matched[:10]


def extract_evaluation_criteria(text: str) -> List[str]:
    """
    Extracts proposal evaluation criteria and qualification conditions across the entire document.
    """
    if not text:
        return []

    criteria: List[str] = []
    matches = re.findall(r'(?i)(?:solvency|experience|compliance|sla|turnaround|security|iso\s*27001|gdpr|dpdp|references?|soc\s*2|capability|fit|pricing|cost)\b[^\n\.;]{5,120}', text)
    for m in matches:
        clean = m.strip()
        if len(clean) >= 15:
            criteria.append(clean)

    seen = set()
    deduped = []
    for c in criteria:
        low = c.lower()
        if low not in seen:
            seen.add(low)
            deduped.append(c)

    return deduped[:8] if deduped else []


def extract_insurance_products(text: str) -> List[str]:
    """Identifies mentioned insurance product lines from proposal text."""
    if not text:
        return []
    product_keywords = [
        ("Commercial Property", ["commercial property", "property damage", "building coverage", "business property"]),
        ("General Liability", ["general liability", "public liability", "commercial liability"]),
        ("Workers' Compensation", ["workers comp", "workers' comp", "workmen compensation"]),
        ("Cyber & Tech E&O", ["cyber", "data breach", "ransomware", "network security", "technology errors"]),
        ("Commercial Auto / Fleet", ["commercial auto", "fleet", "motor insurance"]),
        ("Life & Pensions", ["life insurance", "term life", "annuity", "pension", "endowment"]),
        ("Health & Benefits", ["health insurance", "group health", "medical benefits"]),
        ("D&O / Management Liability", ["directors and officers", "d&o", "management liability"]),
        ("Reinsurance & Specialty", ["reinsurance", "treaty", "facultative", "specialty lines", "marine", "cargo", "aviation"])
    ]
    text_lower = text.lower()
    found = []
    for prod_name, terms in product_keywords:
        if any(t in text_lower for t in terms):
            found.append(prod_name)
    return found[:6]


def extract_evaluation_weights(text: str) -> List[str]:
    """Extracts evaluation weights and scoring percentages across full document."""
    if not text:
        return []
    weights = []
    matches = re.findall(r'(?i)(?:^|\n)\s*([A-Za-z\s/&]{3,35})\s*[:\-–]\s*(\d{1,3}\s*%)', text)
    for category, pct in matches:
        clean_cat = category.strip()
        if any(kw in clean_cat.lower() for kw in ["technical", "commercial", "price", "financial", "experience", "solution", "functional", "implementation", "architecture", "compliance", "claims", "underwriting", "quality", "vendor"]):
            weights.append(f"{clean_cat}: {pct.strip()}")
    return weights[:8]


def extract_timeline(text: str) -> List[str]:
    """Extracts timeline, milestones, and deadlines across full document."""
    if not text:
        return []
    milestones = []
    # Pattern 1: Match key milestone line items (e.g. "Vendor Selection: 45 Days")
    matches = re.findall(r'(?i)(?:^|\n)\s*([A-Za-z0-9\s/–-]{3,40}(?:timeline|schedule|milestone|deadline|go\-live|duration|phase\s*\d|rollout|selection|kickoff)[A-Za-z0-9\s/–-]{0,20})\s*[:\-–]+\s*([^\n\.;]{3,100})', text)
    for label, val in matches:
        clean_lbl = label.strip()
        clean_val = val.strip()
        if clean_lbl and clean_val:
            milestones.append(f"{clean_lbl}: {clean_val}")

    # Pattern 2: Generic timeline statements
    if len(milestones) < 3:
        stmt_matches = re.findall(r'(?i)(?:timeline|schedule|milestone|deadline|go\-live|duration|phase\s*\d|rollout)\s*[:\-–\n]+([^\n\.;]{4,140})', text)
        for m in stmt_matches:
            clean = m.strip()
            if clean and len(clean) >= 4:
                milestones.append(clean)

    seen = set()
    deduped = []
    for m in milestones:
        low = m.lower()
        if low not in seen:
            seen.add(low)
            deduped.append(m)

    return deduped[:8]



def extract_business_problems(text: str) -> List[str]:
    """Extracts identified business problems or operational challenges across full document."""
    if not text:
        return []
    problems = []
    matches = re.findall(r'(?i)(?:challenge|pain\s*point|problem|deficiency|bottleneck|manual\s*process|turnaround\s*delay|legacy\s*system)\s*[:\-–\n]+([^\n\.;]{10,140})', text)
    for m in matches:
        clean = m.strip()
        if clean and len(clean) >= 10:
            problems.append(clean)
    return problems[:6]


def build_proposal_profile(
    file_bytes: bytes,
    filename: str,
    raw_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for Proposal Service.
    Validates document, applies hierarchical chunking and section-based aggregation,
    and generates a rich, structured Proposal Profile encompassing 16 critical proposal dimensions.
    """
    # 1. Validation Gate
    validation = validate_pdf(file_bytes, filename)
    if not validation["valid"]:
        raise ValueError(validation["error"])

    # 2. Text Extraction & Aggregation
    text = raw_text or extract_text(file_bytes, filename)
    if not text or len(text.strip()) < 20:
        raise ValueError("The uploaded proposal does not contain sufficient readable content for analysis.")

    sections = extract_sections(text)
    classified_sections = classify_and_aggregate_sections(text)
    rule_reqs = extract_requirements(text)
    rule_objs = extract_objectives(text)
    rule_caps = extract_capabilities(text)
    rule_criteria = extract_evaluation_criteria(text)
    rule_prods = extract_insurance_products(text)
    rule_weights = extract_evaluation_weights(text)
    rule_timeline = extract_timeline(text)
    rule_problems = extract_business_problems(text)

    # Detect title and target prospect from text
    title_match = re.search(r'(?i)(?:proposal\s+title|rfp\s+title|subject|re:)\s*[:\-\n]+([^\n]+)', text)
    detected_title = title_match.group(1).strip() if title_match else ""
    if not detected_title:
        first_lines = [l.strip() for l in text.split('\n') if l.strip()]
        if first_lines and len(first_lines[0]) < 100:
            detected_title = first_lines[0]
        else:
            clean_fname = re.sub(r'\.(pdf|docx|doc|txt)$', '', filename, flags=re.IGNORECASE)
            detected_title = clean_fname.replace("_", " ").title()

    target_match = re.search(r'(?i)(?:target\s+prospect|insured|issuing\s+authority|company\s+name)\s*[:\-\n]+([^\n]+)', text)
    target_prospect = target_match.group(1).strip() if target_match else None

    # Detect domain context
    domain_context = "Commercial Insurance"
    text_lower = text.lower()
    if "life" in text_lower and "commercial" not in text_lower:
        domain_context = "Life & Pension Insurance"
    elif "health" in text_lower and "commercial" not in text_lower:
        domain_context = "Health Insurance"
    elif "reinsurance" in text_lower:
        domain_context = "Reinsurance & Specialty Lines"

    # 3. LLM Synthesis using Full-Document Hierarchically Aggregated Context
    aggregated_context = build_aggregated_proposal_context(text)
    llm_prompt = f"""You are an expert insurance RFP and proposal analysis specialist.
Analyze the following multi-section aggregated insurance proposal/RFP document context spanning the entire document and extract a comprehensive, structured Proposal Profile.

AGGREGATED DOCUMENT CONTEXT:
--------------------------------------------------
{aggregated_context}
--------------------------------------------------

Extract and return a strict JSON object with this exact schema:
{{
  "proposal_title": "Clear descriptive title of RFP / Proposal",
  "domain": "e.g. Commercial Insurance / Life Insurance / General Insurance / Health Insurance",
  "summary": "2-3 sentence executive overview of what this proposal/RFP requires",
  "insurance_products": ["Commercial Property", "Cyber", ...],
  "business_objectives": ["Primary business objective 1", ...],
  "business_problems": ["Key operational problem / challenge to solve", ...],
  "functional_requirements": ["Underwriting / claims functional requirement 1", ...],
  "technology_requirements": ["Cloud modernization, API-first architecture", ...],
  "ai_ml_requirements": ["AI-driven risk scoring, cognitive intake", ...],
  "data_requirements": ["Enterprise data lake, real-time analytics", ...],
  "integration_requirements": ["Integration with core admin systems", ...],
  "security_requirements": ["SOC 2, ISO 27001, end-to-end encryption", ...],
  "regulatory_requirements": ["IRDAI / Solvency II / DPDP compliance", ...],
  "implementation_requirements": ["Delivery methodology, rollout schedule", ...],
  "evaluation_criteria": ["Technical fit (40%)", "Vendor capability (30%)", ...],
  "evaluation_weights": ["Technical: 40%", "Financial: 30%", ...],
  "commercial_requirements": ["Fixed-price proposal, SLA warranties", ...],
  "timeline": ["RFP submission: 30 days", "Go-live: 6 months", ...]
}}
"""
    ai_profile = None
    try:
        ai_resp = query_gemini(llm_prompt, json_output=True, timeout=35)
        if isinstance(ai_resp, dict) and "proposal_title" in ai_resp:
            ai_profile = ai_resp
    except Exception as e:
        logger.warning("[ProposalService] Gemini extraction issue: %s", e)

    if not ai_profile:
        try:
            ollama_resp = query_ollama(llm_prompt, json_output=True, timeout=30, model_name=PRIMARY_OLLAMA_MODEL)
            if isinstance(ollama_resp, dict) and "proposal_title" in ollama_resp:
                ai_profile = ollama_resp
        except Exception as e:
            logger.warning("[ProposalService] Ollama extraction issue: %s", e)

    # 4. Merge Rule + AI extractions
    final_title = (ai_profile.get("proposal_title") if ai_profile else None) or detected_title or "Commercial Insurance RFP / Proposal"
    final_domain = (ai_profile.get("domain") if ai_profile else None) or domain_context
    final_summary = (ai_profile.get("summary") if ai_profile else None) or f"Commercial insurance proposal ({final_title}) detailing solution requirements, underwriting specifications, and operational scope."
    
    # 16-field Structured Proposal Profile
    insurance_products = (ai_profile.get("insurance_products") if ai_profile and ai_profile.get("insurance_products") else None) or rule_prods
    business_objectives = (ai_profile.get("business_objectives") if ai_profile and ai_profile.get("business_objectives") else None) or rule_objs
    business_problems = (ai_profile.get("business_problems") if ai_profile and ai_profile.get("business_problems") else None) or rule_problems
    functional_reqs = (ai_profile.get("functional_requirements") if ai_profile and ai_profile.get("functional_requirements") else None) or rule_reqs
    tech_reqs = (ai_profile.get("technology_requirements") if ai_profile and ai_profile.get("technology_requirements") else None) or [r for r in rule_reqs if any(k in r.lower() for k in ["cloud", "api", "platform", "system"])]
    ai_ml_reqs = (ai_profile.get("ai_ml_requirements") if ai_profile and ai_profile.get("ai_ml_requirements") else None) or [r for r in rule_reqs if any(k in r.lower() for k in ["ai", "ml", "machine learning", "algorithm", "cognitive", "predictive"])]
    data_reqs = (ai_profile.get("data_requirements") if ai_profile and ai_profile.get("data_requirements") else None) or [r for r in rule_reqs if any(k in r.lower() for k in ["data", "analytics", "warehouse", "lake", "reporting"])]
    integration_reqs = (ai_profile.get("integration_requirements") if ai_profile and ai_profile.get("integration_requirements") else None) or [r for r in rule_reqs if any(k in r.lower() for k in ["integrate", "api", "interface", "core system"])]
    security_reqs = (ai_profile.get("security_requirements") if ai_profile and ai_profile.get("security_requirements") else None) or [r for r in rule_reqs if any(k in r.lower() for k in ["security", "encrypt", "soc", "iso", "cyber"])]
    regulatory_reqs = (ai_profile.get("regulatory_requirements") if ai_profile and ai_profile.get("regulatory_requirements") else None) or [r for r in rule_reqs if any(k in r.lower() for k in ["compliance", "regulat", "audit", "statutory", "gdpr", "dpdp", "solvency"])]
    impl_reqs = (ai_profile.get("implementation_requirements") if ai_profile and ai_profile.get("implementation_requirements") else None) or [r for r in rule_reqs if any(k in r.lower() for k in ["implement", "deploy", "rollout", "vendor", "sla"])]
    eval_criteria = (ai_profile.get("evaluation_criteria") if ai_profile and ai_profile.get("evaluation_criteria") else None) or rule_criteria
    eval_weights = (ai_profile.get("evaluation_weights") if ai_profile and ai_profile.get("evaluation_weights") else None) or rule_weights
    commercial_reqs = (ai_profile.get("commercial_requirements") if ai_profile and ai_profile.get("commercial_requirements") else None) or [r for r in rule_reqs if any(k in r.lower() for k in ["commercial", "pricing", "cost", "fee", "budget"])]
    timeline = (ai_profile.get("timeline") if ai_profile and ai_profile.get("timeline") else None) or rule_timeline
    proposal_id = f"RFP-{uuid.uuid4().hex[:8].upper()}"
    authoritative_chunks = create_canonical_chunks(text)

    profile: Dict[str, Any] = {
        "proposal_id": proposal_id,
        "proposal_title": final_title,
        "filename": filename,
        "file_size": len(file_bytes),
        "page_count": validation.get("page_count", 1),
        "domain": final_domain,
        "summary": final_summary,
        
        # 16-field Structured Profile Specification
        "insurance_products": insurance_products,
        "business_objectives": business_objectives,
        "business_problems": business_problems,
        "functional_requirements": functional_reqs,
        "technology_requirements": tech_reqs,
        "ai_ml_requirements": ai_ml_reqs,
        "data_requirements": data_reqs,
        "integration_requirements": integration_reqs,
        "security_requirements": security_reqs,
        "regulatory_requirements": regulatory_reqs,
        "implementation_requirements": impl_reqs,
        "evaluation_criteria": eval_criteria,
        "evaluation_weights": eval_weights,
        "commercial_requirements": commercial_reqs,
        "timeline": timeline,

        # Dual-branch canonical & authoritative chunking
        "canonical_text": text,
        "authoritative_chunks": authoritative_chunks,

        # Backward compatibility fields
        "objectives": business_objectives,
        "requirements": functional_reqs,
        "capabilities": (ai_profile.get("capabilities") if ai_profile and ai_profile.get("capabilities") else None) or rule_caps,
        
        "target_insured": target_prospect,
        "sections": sections,
        "raw_text_preview": text[:1200]
    }

    logger.info("[ProposalService] Built 16-field Proposal Profile for '%s' (ID: %s, %d requirements, %d authoritative chunks)",
                final_title, proposal_id, len(functional_reqs), len(authoritative_chunks))
    return profile

