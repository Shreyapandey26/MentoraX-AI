"""
Views for MentoraX AI.

Flow:
  /           -> biometric_scan  (GET: show scan page)
  /authorize/ -> authorize       (POST: fake auth, set session, redirect to /input/)
  /input/     -> data_input      (GET: show form | POST: validate, analyze, redirect to /dashboard/)
  /dashboard/ -> dashboard       (GET: show results from session)
  /logout/    -> logout_user     (GET: clear session, go back to /)
"""

import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import BiometricForm, StudentDataForm
from .models import StudentRecord
from .rag_service import get_rag_analysis
from .ocr_service import extract_from_image


# ─────────────────────────────────────────────────────────
# MODULE 1: Biometric Authorization Module
# ─────────────────────────────────────────────────────────

def biometric_scan(request):
    """
    Renders the biometric authorization page.
    This is the entry point / home page of the system.
    """
    # If user is already authorized, skip to input
    if request.session.get("authorized"):
        return redirect("data_input")

    form = BiometricForm()
    return render(request, "biometric.html", {"form": form})


def authorize(request):
    """
    Handles the biometric form submission.
    In a real system this would call hardware APIs to verify fingerprint/iris.
    Here we just validate the name and mark the session as authorized.
    """
    if request.method != "POST":
        return redirect("biometric_scan")

    form = BiometricForm(request.POST)
    if form.is_valid():
        student_name = form.cleaned_data["student_name"].strip()

        # Set session - this is how we "remember" the logged in user
        request.session["authorized"] = True
        request.session["student_name"] = student_name

        # Session lasts for this browser session only
        return redirect("data_input")

    # If form invalid, go back to scan page with the form errors
    return render(request, "biometric.html", {"form": form})


# ─────────────────────────────────────────────────────────
# MODULE 2: Data Acquisition & OCR Module
# ─────────────────────────────────────────────────────────

def data_input(request):
    """
    Shows the data entry form.
    GET  -> render empty form
    POST -> validate data, run diagnostic engine, save to DB, go to dashboard
    """
    # Security check: user must have passed biometric first
    if not request.session.get("authorized"):
        messages.error(request, "Please authorize via biometric scan first.")
        return redirect("biometric_scan")

    if request.method == "POST":
        form = StudentDataForm(request.POST, request.FILES)

        if form.is_valid():
            # Pull out the clean values
            data = form.cleaned_data

            # ──────────────────────────────────────────────
            # MODULE 3: Heuristic Diagnostic Engine
            # This is where we analyze the academic data
            # ──────────────────────────────────────────────
            analysis = run_diagnostic_engine(data)

            # ──────────────────────────────────────────────
            # MODULE 3b: LangChain RAG + Groq LLM Analysis
            # BM25 retrieves relevant knowledge → Groq augments
            # ──────────────────────────────────────────────
            rag_result = get_rag_analysis(data, analysis)
            analysis["ai_summary"]         = rag_result["rag_summary"]
            analysis["ai_recommendations"] = rag_result["rag_recommendations"]
            analysis["ai_study_plan"]      = rag_result["rag_study_plan"]
            analysis["ai_sources"]         = rag_result["rag_sources"]
            analysis["ai_error"]           = rag_result["rag_error"]

            # Save the record to the database
            record = StudentRecord(
                student_name=request.session.get("student_name", "Unknown"),
                student_id=data["student_id"],
                subject_name=data["subject_name"],
                marks_obtained=data["marks_obtained"],
                total_marks=data["total_marks"],
                attendance_percent=data["attendance_percent"],
                study_hours_per_week=data["study_hours_per_week"],
                performance_percent=analysis["percentage"],
                tier=analysis["tier"],
            )
            record.save()

            # Store analysis result in session so dashboard can read it
            request.session["analysis"] = analysis
            request.session["student_id"] = data["student_id"]
            request.session["subject_name"] = data["subject_name"]
            request.session["marks_obtained"] = data["marks_obtained"]
            request.session["total_marks"] = data["total_marks"]
            request.session["attendance_percent"] = data["attendance_percent"]
            request.session["study_hours_per_week"] = data["study_hours_per_week"]

            return redirect("dashboard")

        # Form has errors - re-render with error messages shown
        return render(request, "input.html", {
            "form": form,
            "student_name": request.session.get("student_name"),
        })

    # GET request - show blank form
    form = StudentDataForm()
    return render(request, "input.html", {
        "form": form,
        "student_name": request.session.get("student_name"),
    })


# ─────────────────────────────────────────────────────────
# MODULE 3: Heuristic Diagnostic Engine (Helper Function)
# ─────────────────────────────────────────────────────────

def run_diagnostic_engine(data):
    """
    The brain of MentoraX AI.
    Takes raw student data and returns a full analysis dictionary.

    Steps:
    1. Calculate performance percentage
    2. Classify into tier
    3. Correlation mapping (habits vs results)
    4. Generate recommendations
    """

    marks = data["marks_obtained"]
    total = data["total_marks"]
    attendance = data["attendance_percent"]
    study_hours = data["study_hours_per_week"]

    # Step 1: Calculate performance percentage
    percentage = round((marks / total) * 100, 2)

    # Step 2: Classify into tier
    if percentage >= 75:
        tier = "Excellent"
        tier_color = "#00ff88"       # Green
        tier_icon = "★"
    elif percentage >= 50:
        tier = "Average"
        tier_color = "#ffaa00"       # Orange
        tier_icon = "◆"
    else:
        tier = "Alert"
        tier_color = "#ff4444"       # Red
        tier_icon = "⚠"

    # Step 3: Correlation mapping
    # We look at patterns between habits and performance
    correlations = []

    # Attendance correlation
    if attendance < 75:
        correlations.append({
            "type": "danger",
            "icon": "📉",
            "finding": f"Low attendance ({attendance}%) is likely impacting exam performance.",
            "detail": "Students below 75% attendance statistically score 15-20% lower."
        })
    elif attendance >= 90:
        correlations.append({
            "type": "success",
            "icon": "✅",
            "finding": f"Excellent attendance ({attendance}%) is a strong positive factor.",
            "detail": "High attendance correlates with better concept clarity."
        })
    else:
        correlations.append({
            "type": "info",
            "icon": "📊",
            "finding": f"Attendance ({attendance}%) is satisfactory.",
            "detail": "Aim for 90%+ to maximize learning consistency."
        })

    # Study hours correlation
    if study_hours < 7:
        correlations.append({
            "type": "danger",
            "icon": "⏱️",
            "finding": f"Very low study hours ({study_hours} hrs/week) detected.",
            "detail": "Experts recommend 15-20 hours per week for average difficulty subjects."
        })
    elif study_hours >= 20:
        correlations.append({
            "type": "success",
            "icon": "📚",
            "finding": f"High study effort ({study_hours} hrs/week) noted.",
            "detail": "Consistent with top-performing student profiles."
        })
    else:
        correlations.append({
            "type": "info",
            "icon": "📖",
            "finding": f"Study hours ({study_hours} hrs/week) are moderate.",
            "detail": "Consider increasing to 20+ hours for better retention."
        })

    # Cross-correlation: high study hours but low marks
    if study_hours >= 15 and percentage < 50:
        correlations.append({
            "type": "warning",
            "icon": "🔍",
            "finding": "Study hours are high but performance is low — study method may be inefficient.",
            "detail": "Consider active recall, spaced repetition, or seeking tutoring help."
        })

    # Cross-correlation: low study hours but good marks
    if study_hours < 10 and percentage >= 75:
        correlations.append({
            "type": "info",
            "icon": "💡",
            "finding": "Good performance with fewer study hours — natural aptitude or prior knowledge.",
            "detail": "Maintain consistency; don't rely solely on natural ability for harder semesters."
        })

    # Step 4: Generate study recommendations
    recommendations = generate_recommendations(tier, attendance, study_hours, percentage)

    # Prepare chart data for Chart.js (passed as JSON to the template)
    # Doughnut chart: marks obtained vs marks missed
    doughnut_data = {
        "obtained": marks,
        "missed": round(total - marks, 2),
        "total": total,
    }

    # Bar chart: multiple metrics normalized to show side by side
    # We normalize study hours to a 0-100 scale (assuming 30 hrs/week = 100%)
    study_hours_normalized = min(round((study_hours / 30) * 100, 2), 100)
    bar_data = {
        "labels": ["Performance %", "Attendance %", "Study Effort %"],
        "values": [percentage, attendance, study_hours_normalized],
    }

    return {
        "percentage": percentage,
        "tier": tier,
        "tier_color": tier_color,
        "tier_icon": tier_icon,
        "correlations": correlations,
        "recommendations": recommendations,
        "doughnut_data": doughnut_data,
        "bar_data": bar_data,
    }


def generate_recommendations(tier, attendance, study_hours, percentage):
    """
    Returns a list of personalized study strategy suggestions
    based on the student's tier and habit data.
    """
    recs = []

    if tier == "Alert":
        recs.append("🚨 Immediate Action: Schedule a meeting with your faculty/mentor this week.")
        recs.append("📅 Create a strict daily timetable with at least 3-hour study blocks.")
        recs.append("🔁 Use the Pomodoro technique: 25 min study → 5 min break.")

    if tier == "Average":
        recs.append("📈 You're close to Excellent — push study hours to 20+/week.")
        recs.append("📝 Attempt previous year question papers regularly.")
        recs.append("🤝 Form a study group to improve weak topics collaboratively.")

    if tier == "Excellent":
        recs.append("🏆 Outstanding performance! Consider mentoring peers.")
        recs.append("🎯 Focus on competitive exams or research projects for extra edge.")

    if attendance < 75:
        recs.append("🏫 Priority: Improve attendance — aim for minimum 75% this week.")

    if study_hours < 10:
        recs.append("⏰ Increase daily study time — even 2 extra hours per day makes a big difference.")

    # Always add one general tip
    recs.append("💤 Don't compromise on sleep — 7-8 hours ensures better memory consolidation.")

    return recs


# ─────────────────────────────────────────────────────────
# MODULE 4: Neural HUD (Dashboard View)
# ─────────────────────────────────────────────────────────

def dashboard(request):
    """
    Renders the dashboard with all the analysis results.
    Chart.js renders the doughnut and bar charts from the data we pass.
    """
    if not request.session.get("authorized"):
        return redirect("biometric_scan")

    analysis = request.session.get("analysis")
    if not analysis:
        messages.warning(request, "No analysis data found. Please enter student data first.")
        return redirect("data_input")

    context = {
        "student_name": request.session.get("student_name"),
        "student_id": request.session.get("student_id"),
        "subject_name": request.session.get("subject_name"),
        "marks_obtained": request.session.get("marks_obtained"),
        "total_marks": request.session.get("total_marks"),
        "attendance_percent": request.session.get("attendance_percent"),
        "study_hours_per_week": request.session.get("study_hours_per_week"),
        "analysis": analysis,
    }

    return render(request, "dashboard.html", context)


def logout_user(request):
    """
    Clears the session and sends user back to home page.
    """
    request.session.flush()
    return redirect("home_page")


# ─────────────────────────────────────────────────────────
# Home Page
# ─────────────────────────────────────────────────────────

def home_page(request):
    """Landing / home page — visible to everyone, no auth required."""
    # Count total analyses done so far
    total_analyses = StudentRecord.objects.count()
    return render(request, "home.html", {"total_analyses": total_analyses})


# ─────────────────────────────────────────────────────────
# About Page
# ─────────────────────────────────────────────────────────

def about_page(request):
    """About page — project info, tech stack, team."""
    return render(request, "about.html")


# ─────────────────────────────────────────────────────────
# OCR Endpoint — AJAX only
# ─────────────────────────────────────────────────────────

@require_POST
def ocr_scan(request):
    """
    Accepts a POST with an image file under key 'marksheet'.
    Runs OCR and returns extracted fields as JSON.
    """
    if not request.session.get("authorized"):
        return JsonResponse({"error": "Not authorized"}, status=403)

    image_file = request.FILES.get("marksheet")
    if not image_file:
        return JsonResponse({"error": "No image uploaded"}, status=400)

    result = extract_from_image(image_file)
    return JsonResponse(result)
