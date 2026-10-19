"""
Groq AI Service for MentoraX AI.

Uses llama-3.3-70b-versatile (Groq's fastest + most capable free model)
to generate a personalized AI analysis report for each student.

Call: get_ai_analysis(student_data, heuristic_analysis)
Returns: dict with ai_summary, ai_recommendations, ai_study_plan
"""

import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


# ─── Groq model to use ───────────────────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"


def get_ai_analysis(student_data: dict, heuristic: dict) -> dict:
    """
    Calls the Groq API and returns AI-generated insights.

    Parameters:
        student_data  – cleaned form data (marks, attendance, etc.)
        heuristic     – result dict from run_diagnostic_engine()

    Returns:
        {
            "ai_summary":         str,   # 2-3 sentence personalised summary
            "ai_recommendations": list,  # 4-6 bullet-point strings
            "ai_study_plan":      list,  # 5-day study plan items
            "ai_error":           str,   # non-empty only when API fails
        }
    """
    api_key = settings.GROQ_API_KEY
    if not api_key or api_key == "your_groq_api_key_here":
        return _fallback("GROQ_API_KEY not set. Add your key to the .env file.")

    try:
        from groq import Groq
    except ImportError:
        return _fallback("groq package not installed. Run: pip install groq")

    prompt = _build_prompt(student_data, heuristic)

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are MentoraX AI, an expert academic performance analyst. "
                        "You give clear, empathetic, and actionable advice to students. "
                        "Always respond with valid JSON only — no extra text, no markdown fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.65,
            max_tokens=1024,
        )

        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)

        return {
            "ai_summary": result.get("summary", ""),
            "ai_recommendations": result.get("recommendations", []),
            "ai_study_plan": result.get("study_plan", []),
            "ai_error": "",
        }

    except json.JSONDecodeError as e:
        logger.error("Groq response was not valid JSON: %s", e)
        return _fallback("AI returned an unexpected format. Try again.")
    except Exception as e:
        logger.error("Groq API error: %s", e)
        return _fallback(f"AI service error: {str(e)}")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_prompt(data: dict, h: dict) -> str:
    return f"""
A student has submitted their academic data. Analyse it and respond with a
JSON object that has exactly these three keys:

{{
  "summary": "<2-3 sentence personalised overview of the student's situation>",
  "recommendations": ["<rec 1>", "<rec 2>", "<rec 3>", "<rec 4>", "<rec 5>"],
  "study_plan": [
    "Day 1: <specific task>",
    "Day 2: <specific task>",
    "Day 3: <specific task>",
    "Day 4: <specific task>",
    "Day 5: <specific task>"
  ]
}}

Student Data:
- Subject: {data.get('subject_name', 'N/A')}
- Marks Obtained: {data.get('marks_obtained')} / {data.get('total_marks')}
- Performance: {h.get('percentage')}%
- Academic Tier: {h.get('tier')}
- Attendance: {data.get('attendance_percent')}%
- Study Hours per Week: {data.get('study_hours_per_week')}

Correlation findings already identified by the heuristic engine:
{chr(10).join(f"- {c['finding']}" for c in h.get('correlations', []))}

Rules:
- Be encouraging but honest.
- Recommendations must be specific and actionable (not generic).
- Study plan tasks must be concrete (e.g. "Solve 10 past-paper questions on topic X").
- Respond with raw JSON only — no markdown, no extra explanation.
"""


def _fallback(error_msg: str) -> dict:
    return {
        "ai_summary": "",
        "ai_recommendations": [],
        "ai_study_plan": [],
        "ai_error": error_msg,
    }
