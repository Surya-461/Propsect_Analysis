"""
Proposal Retrieval Service for Proposal-Based Prospect Analysis.
Implements the Authoritative Branch:
- Canonical document chunking with page and section preservation
- Hierarchical + Dense/BM25 retrieval against the 15-parameter catalog
- Extraction of verbatim RFP requirement clauses and candidate evidence
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from rank_bm25 import BM25Okapi

from config.proposal_analysis_config import (
    PROPOSAL_PARAMETERS_CATALOG,
    PROPOSAL_PARAMETERS_BY_ID
)

logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with", "by", "of", "from",
    "as", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "shall", "should", "may", "might", "must", "can", "could", "this",
    "that", "these", "those", "it", "its", "they", "them", "their", "we", "us", "our", "you", "your"
}


def tokenize_for_bm25(text: str) -> List[str]:
    """Tokenizes text for BM25 ranking, cleaning punctuation and lowercasing."""
    if not text:
        return []
    words = re.findall(r'[a-zA-Z0-9_\-\.]{2,}', text.lower())
    return [w for w in words if w not in STOPWORDS]


def create_canonical_chunks(
    text: str,
    chunk_size: int = 900,
    overlap: int = 150
) -> List[Dict[str, Any]]:
    """
    Splits the canonical document into authoritative chunks, tracking page numbers
    and section hints where available.
    """
    if not text or not text.strip():
        return []

    # Check for page markers
    page_segments = re.split(r'(?:^|\n)---\s*Page\s*(\d+)\s*---', text)
    has_page_markers = len(page_segments) > 2

    raw_pages: List[Tuple[int, str]] = []
    if has_page_markers:
        # Structure: [preamble, page_num1, text1, page_num2, text2, ...]
        pre = page_segments[0].strip()
        if pre:
            raw_pages.append((1, pre))
        for i in range(1, len(page_segments), 2):
            try:
                p_num = int(page_segments[i])
            except ValueError:
                p_num = (i // 2) + 1
            p_text = page_segments[i + 1] if i + 1 < len(page_segments) else ""
            if p_text.strip():
                raw_pages.append((p_num, p_text.strip()))
    else:
        # Single continuous document text
        raw_pages.append((1, text.strip()))

    chunks: List[Dict[str, Any]] = []
    chunk_counter = 0

    for page_num, p_text in raw_pages:
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', p_text) if p.strip()]
        if not paragraphs:
            paragraphs = [p_text]

        current_text = ""
        current_section_hint = "General"

        for para in paragraphs:
            # Check for header/section line
            header_match = re.match(r'^(?:[0-9]+[\.\)]\s+|section\s+[0-9a-z]+[\.:\s]+|[A-Z\s]{4,35}[:\-])\s*(.+)$', para, re.IGNORECASE)
            if header_match:
                current_section_hint = para[:60].strip()

            if len(current_text) + len(para) + 2 <= chunk_size:
                current_text = f"{current_text}\n\n{para}".strip()
            else:
                if current_text:
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_counter}",
                        "chunk_index": chunk_counter,
                        "page_number": page_num,
                        "section_hint": current_section_hint,
                        "text": current_text,
                        "token_count": len(current_text.split())
                    })
                    chunk_counter += 1
                    overlap_portion = current_text[-overlap:] if len(current_text) > overlap else current_text
                    current_text = f"{overlap_portion}\n\n{para}".strip()
                else:
                    # Paragraph itself is larger than chunk_size, split by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    for sent in sentences:
                        if len(current_text) + len(sent) + 1 <= chunk_size:
                            current_text = f"{current_text} {sent}".strip()
                        else:
                            if current_text:
                                chunks.append({
                                    "chunk_id": f"chunk_{chunk_counter}",
                                    "chunk_index": chunk_counter,
                                    "page_number": page_num,
                                    "section_hint": current_section_hint,
                                    "text": current_text,
                                    "token_count": len(current_text.split())
                                })
                                chunk_counter += 1
                                overlap_portion = current_text[-overlap:] if len(current_text) > overlap else current_text
                                current_text = f"{overlap_portion} {sent}".strip()
                            else:
                                chunks.append({
                                    "chunk_id": f"chunk_{chunk_counter}",
                                    "chunk_index": chunk_counter,
                                    "page_number": page_num,
                                    "section_hint": current_section_hint,
                                    "text": sent[:chunk_size],
                                    "token_count": len(sent[:chunk_size].split())
                                })
                                chunk_counter += 1
                                current_text = sent[chunk_size - overlap:]

        if current_text:
            chunks.append({
                "chunk_id": f"chunk_{chunk_counter}",
                "chunk_index": chunk_counter,
                "page_number": page_num,
                "section_hint": current_section_hint,
                "text": current_text,
                "token_count": len(current_text.split())
            })
            chunk_counter += 1

    return chunks


def extract_chunks_from_profile(proposal_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts or reconstructs authoritative document chunks from a proposal profile.
    Supports:
    1. Pre-computed authoritative_chunks in profile
    2. Full canonical_text in profile
    3. Reconstructed chunks from requirements, objectives, capabilities, and sections
    """
    if not proposal_profile:
        return []

    # 1. Existing pre-computed chunks
    if "authoritative_chunks" in proposal_profile and isinstance(proposal_profile["authoritative_chunks"], list) and proposal_profile["authoritative_chunks"]:
        return proposal_profile["authoritative_chunks"]

    # 2. Canonical text
    canonical_text = proposal_profile.get("canonical_text") or proposal_profile.get("raw_text") or proposal_profile.get("extracted_text")
    if canonical_text and len(canonical_text.strip()) > 50:
        return create_canonical_chunks(canonical_text)

    # 3. Fallback: synthesize chunks from structured fields
    synth_parts: List[str] = []
    
    title = proposal_profile.get("proposal_title") or proposal_profile.get("proposal_name") or ""
    summary = proposal_profile.get("summary") or ""
    if title or summary:
        synth_parts.append(f"Proposal: {title}\nSummary: {summary}")

    objs = proposal_profile.get("business_objectives") or proposal_profile.get("objectives") or []
    if objs:
        synth_parts.append("Business Objectives:\n" + "\n".join(f"- {o}" for o in objs))

    reqs = proposal_profile.get("functional_requirements") or proposal_profile.get("requirements") or []
    if reqs:
        if isinstance(reqs, dict):
            req_lines = [f"{k}: {v}" for k, v in reqs.items()]
            synth_parts.append("Functional Requirements:\n" + "\n".join(f"- {r}" for r in req_lines))
        elif isinstance(reqs, list):
            synth_parts.append("Functional Requirements:\n" + "\n".join(f"- {r}" for r in reqs))

    for field in [
        "technology_requirements", "ai_ml_requirements", "data_requirements",
        "integration_requirements", "security_requirements", "regulatory_requirements",
        "implementation_requirements", "evaluation_criteria", "commercial_requirements"
    ]:
        val = proposal_profile.get(field)
        if val and isinstance(val, list):
            label = field.replace("_", " ").title()
            synth_parts.append(f"{label}:\n" + "\n".join(f"- {item}" for item in val))

    sections = proposal_profile.get("sections")
    if sections and isinstance(sections, dict):
        for s_name, s_content in sections.items():
            if s_content and isinstance(s_content, str) and len(s_content.strip()) > 30:
                synth_parts.append(f"Section {s_name.title()}:\n{s_content.strip()}")

    synth_text = "\n\n".join(synth_parts)
    if synth_text.strip():
        return create_canonical_chunks(synth_text)

    return []


class RFPChunkRetriever:
    """
    BM25 and Dense Keyword Retriever for Full RFP Chunks.
    """
    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        self.tokenized_corpus = [tokenize_for_bm25(c["text"]) for c in chunks]
        if any(self.tokenized_corpus):
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.bm25 = None

    def retrieve(
        self,
        param_meta: Dict[str, Any],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k authoritative chunks for a parameter and extracts matching sentences.
        """
        if not self.chunks or not self.bm25:
            return []

        param_name = param_meta.get("name", "")
        param_desc = param_meta.get("description", "")
        param_keywords = param_meta.get("keywords", [])
        search_queries = param_meta.get("search_queries", [])

        # Formulate composite query
        query_text = f"{param_name} {param_desc} {' '.join(param_keywords)} {' '.join(search_queries)}"
        tokenized_query = tokenize_for_bm25(query_text)

        if not tokenized_query:
            return []

        bm25_scores = self.bm25.get_scores(tokenized_query)

        scored_chunks = []
        for idx, chunk in enumerate(self.chunks):
            base_score = float(bm25_scores[idx])
            chunk_lower = chunk["text"].lower()

            # Keyword bonus for exact concept matches
            keyword_hits = sum(1 for kw in param_keywords if kw.lower() in chunk_lower)
            combined_score = base_score + (keyword_hits * 1.5)

            if combined_score > 0.1:
                # Extract verbatim matching clauses/sentences
                sentences = re.split(r'(?<=[\n\.\?!])\s+', chunk["text"])
                matching_clauses = []
                for s in sentences:
                    s_clean = s.strip()
                    if len(s_clean) >= 20 and any(kw.lower() in s_clean.lower() for kw in param_keywords):
                        matching_clauses.append(s_clean)

                scored_chunks.append({
                    "chunk": chunk,
                    "score": combined_score,
                    "keyword_hits": keyword_hits,
                    "matching_clauses": matching_clauses[:4]
                })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]


def retrieve_authoritative_catalog_excerpts(
    chunks: List[Dict[str, Any]],
    catalog: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Executes hierarchical and dense retrieval for each of the 15 parameters
    against the full RFP chunks.
    
    Returns a dictionary mapping:
    param_id -> {
        "score": float,
        "excerpts": List[str],
        "top_chunks": List[Dict[str, Any]]
    }
    """
    if not catalog:
        catalog = PROPOSAL_PARAMETERS_CATALOG

    if not chunks:
        return {p["id"]: {"score": 0.0, "excerpts": [], "top_chunks": []} for p in catalog}

    retriever = RFPChunkRetriever(chunks)
    results = {}

    for param in catalog:
        pid = param["id"]
        retrieved = retriever.retrieve(param, top_k=3)
        
        excerpts = []
        seen = set()
        total_score = 0.0

        for item in retrieved:
            total_score = max(total_score, item["score"])
            for clause in item.get("matching_clauses", []):
                cleaned = clause.strip()
                if cleaned.lower() not in seen:
                    seen.add(cleaned.lower())
                    # Format with page reference if available
                    page = item["chunk"].get("page_number", 1)
                    excerpts.append(f"[Page {page}] {cleaned}")

        # If matching clauses didn't catch specific keywords, use snippet from top chunk
        if not excerpts and retrieved and retrieved[0]["score"] > 1.0:
            top_c = retrieved[0]["chunk"]
            snip = top_c["text"][:200].strip().replace("\n", " ")
            excerpts.append(f"[Page {top_c.get('page_number', 1)}] {snip}...")

        results[pid] = {
            "score": round(total_score, 2),
            "excerpts": excerpts[:5],
            "top_chunks": [r["chunk"] for r in retrieved]
        }

    return results
