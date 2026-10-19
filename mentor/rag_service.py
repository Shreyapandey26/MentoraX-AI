"""
RAG Service for MentoraX AI
─────────────────────────────────────────────────────────────────────
Architecture:
  • Knowledge Base   : 7 text files in mentor/knowledge/
  • Text Splitter    : LangChain RecursiveCharacterTextSplitter
  • Retriever        : BM25Retriever (rank_bm25) — no downloads, instant start
  • LLM              : Groq ChatGroq (llama-3.3-70b-versatile)
  • Chain            : LangChain RetrievalQA with custom PromptTemplate

Flow per analysis:
  1. Build (once) or reuse the BM25 retriever from knowledge documents
  2. Query: "{subject} + {tier} + {attendance} + {study_hours}"
  3. Top-3 relevant chunks retrieved
  4. Chunks + student data injected into Groq LLM prompt
  5. LLM returns JSON: summary, recommendations, study_plan, sources
─────────────────────────────────────────────────────────────────────
"""

import os
import json
import logging
import pathlib

from django.conf import settings

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
KNOWLEDGE_DIR = pathlib.Path(__file__).parent / "knowledge"

# ── Module-level retriever cache (built once per server start) ────────────────
_retriever = None
_docs_meta  = []   # parallel list of {source, snippet} for display on dashboard


# ═════════════════════════════════════════════════════════════════════════════
# Public API
# ═════════════════════════════════════════════════════════════════════════════

def get_rag_analysis(student_data: dict, heuristic: dict) -> dict:
    """
    Main entry point.  Returns:
    {
        "rag_summary":         str,
        "rag_recommendations": list[str],   # 5 items
        "rag_study_plan":      list[str],   # 5 days
        "rag_sources":         list[str],   # document titles used
        "rag_context":         str,         # raw retrieved context (debug)
        "rag_error":           str,         # non-empty on failure
    }
    """
    api_key = settings.GROQ_API_KEY
    if not api_key or api_key == "your_groq_api_key_here":
        return _fail("GROQ_API_KEY not set in .env file.")

    try:
        retriever = _get_retriever()
        context, sources = _retrieve_context(student_data, heuristic, retriever)
        result = _call_llm(student_data, heuristic, context, api_key)
        result["rag_sources"]  = sources
        result["rag_context"]  = context
        result["rag_error"]    = ""
        return result
    except Exception as e:
        logger.error("RAG pipeline error: %s", e, exc_info=True)
        return _fail(str(e))


# ═════════════════════════════════════════════════════════════════════════════
# Step 1 — Build / Reuse BM25 Retriever
# ═════════════════════════════════════════════════════════════════════════════

def _get_retriever():
    global _retriever
    if _retriever is not None:
        return _retriever

    from langchain_community.retrievers import BM25Retriever
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document

    if not KNOWLEDGE_DIR.exists():
        raise FileNotFoundError(f"Knowledge directory not found: {KNOWLEDGE_DIR}")

    txt_files = list(KNOWLEDGE_DIR.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError("No .txt files found in knowledge directory.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
        separators=["\n\n", "\n", ". ", " "],
    )

    all_docs = []
    for fpath in txt_files:
        raw = fpath.read_text(encoding="utf-8")
        chunks = splitter.split_text(raw)
        for chunk in chunks:
            all_docs.append(Document(
                page_content=chunk,
                metadata={"source": fpath.stem},
            ))

    logger.info("RAG: Built BM25 retriever with %d chunks from %d files.",
                len(all_docs), len(txt_files))

    _retriever = BM25Retriever.from_documents(all_docs, k=4)
    return _retriever


# ═════════════════════════════════════════════════════════════════════════════
# Step 2 — Build query & retrieve relevant chunks
# ═════════════════════════════════════════════════════════════════════════════

def _retrieve_context(student_data: dict, heuristic: dict, retriever) -> tuple:
    """
    Compose a rich query from student data, retrieve top chunks,
    return (context_text, source_list).
    """
    subject    = student_data.get("subject_name", "general")
    tier       = heuristic.get("tier", "Average")
    attendance = student_data.get("attendance_percent", 75)
    hours      = student_data.get("study_hours_per_week", 10)
    pct        = heuristic.get("percentage", 50)

    # Build a rich BM25 query covering multiple relevant dimensions
    query = (
        f"{subject} study strategy "
        f"{tier.lower()} tier performance score {pct}% "
        f"attendance {attendance}% "
        f"study hours per week {hours} "
        f"{'low attendance recovery' if attendance < 75 else ''} "
        f"{'poor performance recovery' if pct < 50 else ''} "
        f"{'average improvement breakthrough' if 50 <= pct < 75 else ''} "
        f"{'excellent maintain competitive' if pct >= 75 else ''}"
    ).strip()

    docs = retriever.invoke(query)

    # De-duplicate and collect source names
    seen_sources = set()
    context_parts = []
    sources = []

    for doc in docs:
        src = doc.metadata.get("source", "general")
        context_parts.append(f"[{src.upper()}]\n{doc.page_content}")
        if src not in seen_sources:
            seen_sources.add(src)
            sources.append(_format_source_name(src))

    context = "\n\n---\n\n".join(context_parts)
    return context, sources


def _format_source_name(stem: str) -> str:
    mapping = {
        "mathematics":        "Mathematics Study Guide",
        "science_physics":    "Physics Study Guide",
        "science_chemistry":  "Chemistry Study Guide",
        "general_strategies": "General Study Strategies",
        "tier_alert":         "Alert Tier Recovery Plan",
        "tier_average":       "Average Tier Breakthrough",
        "tier_excellent":     "Excellent Tier Peak Performance",
        "attendance_habits":  "Attendance Impact Guide",
        "study_hours":        "Study Hours Optimisation",
    }
    return mapping.get(stem, stem.replace("_", " ").title())


# ═════════════════════════════════════════════════════════════════════════════
# Step 3 — Augmented Groq LLM call
# ═════════════════════════════════════════════════════════════════════════════

def _call_llm(student_data: dict, heuristic: dict, context: str, api_key: str) -> dict:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = ChatGroq(
        api_key=api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=0.60,
        max_tokens=1200,
    )

    system_prompt = (
        "You are MentoraX AI, an expert academic performance coach. "
        "You are given RETRIEVED KNOWLEDGE from a curated study-strategy database "
        "AND the student's actual academic data. "
        "Use the retrieved knowledge to ground your advice in proven strategies. "
        "Respond with valid JSON only — no markdown fences, no extra text."
    )

    user_prompt = f"""
RETRIEVED KNOWLEDGE FROM KNOWLEDGE BASE:
{context}

─────────────────────────────────────────
STUDENT DATA:
- Name context: anonymous student
- Subject: {student_data.get('subject_name', 'N/A')}
- Marks: {student_data.get('marks_obtained')} / {student_data.get('total_marks')}
- Performance: {heuristic.get('percentage')}%
- Academic Tier: {heuristic.get('tier')}
- Attendance: {student_data.get('attendance_percent')}%
- Study Hours/Week: {student_data.get('study_hours_per_week')}

HEURISTIC FINDINGS:
{chr(10).join(f"• {c['finding']}" for c in heuristic.get('correlations', []))}

─────────────────────────────────────────
TASK:
Using the retrieved knowledge above as your primary reference, generate a
personalised academic analysis. Return ONLY this JSON structure:

{{
  "summary": "<2-3 sentence personalised overview grounded in retrieved knowledge>",
  "recommendations": [
    "<specific rec 1 — cite technique from knowledge base>",
    "<specific rec 2>",
    "<specific rec 3>",
    "<specific rec 4>",
    "<specific rec 5>"
  ],
  "study_plan": [
    "Day 1: <concrete task with subject-specific detail>",
    "Day 2: <concrete task>",
    "Day 3: <concrete task>",
    "Day 4: <concrete task>",
    "Day 5: <concrete task>"
  ]
}}

Rules:
- Recommendations must reference specific techniques from the retrieved knowledge.
- Study plan tasks must be concrete and subject-specific, not generic.
- Be encouraging but honest.
- Raw JSON only — no markdown, no preamble.
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    raw = response.content.strip()
    # Strip accidental markdown fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    parsed = json.loads(raw)

    return {
        "rag_summary":         parsed.get("summary", ""),
        "rag_recommendations": parsed.get("recommendations", []),
        "rag_study_plan":      parsed.get("study_plan", []),
    }


# ═════════════════════════════════════════════════════════════════════════════
# Helper
# ═════════════════════════════════════════════════════════════════════════════

def _fail(msg: str) -> dict:
    return {
        "rag_summary":         "",
        "rag_recommendations": [],
        "rag_study_plan":      [],
        "rag_sources":         [],
        "rag_context":         "",
        "rag_error":           msg,
    }
