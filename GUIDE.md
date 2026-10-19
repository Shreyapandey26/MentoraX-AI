# MentoraX AI — Complete Project Guide

> Final Year Project | Django + Chart.js + Groq AI | Academic Performance Diagnostic System

---

## Quick Start (with Groq AI)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Groq API key in .env
#    Get a free key at: https://console.groq.com/keys
#    Open .env and replace: GROQ_API_KEY=your_groq_api_key_here

# 3. Run migrations (first time only)
python manage.py migrate

# 4. Start the server
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

**Flow:**  Biometric Scan → Enter Name → Data Input → Dashboard (charts + AI analysis)

---

## Table of Contents

1. [What is MentoraX AI?](#1-what-is-mentorax-ai)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [How to Run](#4-how-to-run)
5. [URL Flow — How Pages Connect](#5-url-flow--how-pages-connect)
6. [Module 1 — Biometric Authorization](#6-module-1--biometric-authorization)
7. [Module 2 — Data Acquisition & OCR](#7-module-2--data-acquisition--ocr)
8. [Module 3 — Heuristic Diagnostic Engine](#8-module-3--heuristic-diagnostic-engine)
9. [Module 3b — Groq AI Analysis](#9-module-3b--groq-ai-analysis)
10. [Module 4 — Neural HUD (Charts)](#10-module-4--neural-hud-charts)
11. [Database & Model](#11-database--model)
11. [Forms & Validation](#11-forms--validation)
12. [Sessions — How Login State Works](#12-sessions--how-login-state-works)
13. [Templates & Static Files](#13-templates--static-files)
14. [Admin Panel](#14-admin-panel)
15. [Switch to PostgreSQL](#15-switch-to-postgresql)

---

## 1. What is MentoraX AI?

MentoraX AI is a student academic performance analyzer.
A student enters their marks, attendance, and study hours → the system runs analysis →
shows visual charts and tells the student why they scored what they scored and what to do next.

**Problem it solves:** Raw marksheets tell you the number, not the reason.
MentoraX tells you: *"Your attendance was 62% and that's likely why your score is low."*

**It is NOT a live/production app** — it's a developer-level college project built to demonstrate:
- Django MVC pattern
- Session management
- Form validation with custom rules
- Dynamic chart rendering
- Database storage

---

## 2. Tech Stack

| Technology | What it does in this project |
|------------|------------------------------|
| **Python 3.12** | Core language |
| **Django 6.0.2** | Web framework — handles routing, views, templates, ORM |
| **SQLite** | Default database (zero config, file-based) |
| **Chart.js 4.4** | JavaScript library for doughnut + bar charts (loaded via CDN) |
| **HTML/CSS** | Django templates with a dark cyberpunk theme |
| **Django Sessions** | Stores login state and analysis results between page loads |
| **Django Forms** | Handles form rendering, data cleaning, and validation |
| **Django ORM** | Talks to the database without writing SQL |

No external Python packages beyond Django are strictly required.
`Pillow` is listed in `requirements.txt` only because `ImageField` is defined (OCR placeholder) — but it is disabled in the UI so it won't block you.

---

## 3. Project Structure

```
mentorax_ai/                  ← root (your working directory)
│
├── manage.py                 ← Django's command-line tool (run, migrate, etc.)
├── db.sqlite3                ← Database file (auto-created after migrate)
├── requirements.txt          ← Python packages list
├── GUIDE.md                  ← This file
│
├── mentorax_ai/              ← Project config folder (same name as root, confusing but normal)
│   ├── settings.py           ← All Django config (apps, DB, templates, static)
│   ├── urls.py               ← Root URL router — sends traffic to mentor app
│   └── wsgi.py               ← For deploying to a web server (ignore for dev)
│
├── mentor/                   ← Our main Django app (all the real code lives here)
│   ├── models.py             ← Defines StudentRecord database table
│   ├── views.py              ← All logic — 4 modules + diagnostic engine
│   ├── forms.py              ← BiometricForm + StudentDataForm with validation
│   ├── urls.py               ← URL patterns for this app
│   ├── admin.py              ← Registers model so it shows in /admin/
│   └── migrations/
│       └── 0001_initial.py   ← Auto-generated: creates the DB table
│
├── templates/                ← All HTML files
│   ├── base.html             ← Layout template: navbar, footer, flash messages
│   ├── biometric.html        ← Page 1: fingerprint scan + name entry
│   ├── input.html            ← Page 2: student data form
│   └── dashboard.html        ← Page 3: results, charts, correlations
│
└── static/                   ← CSS and JS files
    ├── css/
    │   └── style.css         ← Full dark-theme styling for all pages
    └── js/
        └── biometric.js      ← startScan() animation logic
```

**Key rule:** Django always looks for templates in the `templates/` folder
and static files in the `static/` folder — we configured both in `settings.py`.

---

## 4. How to Run

```bash
# Step 1: Navigate to project root
cd D:/webcoss/MentoraX_AI/mentorax_ai

# Step 2: Install Django if not already installed
pip install django

# Step 3: Create the database tables
python manage.py migrate

# Step 4: (Optional) Create admin user to access /admin/
python manage.py createsuperuser

# Step 5: Start the development server
python manage.py runserver
```

Then open your browser: **http://127.0.0.1:8000/**

> The dev server auto-reloads when you edit Python files. No restart needed.

---

## 5. URL Flow — How Pages Connect

```
Browser                Django                 What happens
──────────────────────────────────────────────────────────────
GET  /             →  biometric_scan()    →  Show fingerprint scan page
POST /authorize/   →  authorize()         →  Validate name, set session, redirect
GET  /input/       →  data_input()        →  Show the data entry form
POST /input/       →  data_input()        →  Validate form, run engine, save DB, redirect
GET  /dashboard/   →  dashboard()         →  Show results from session
GET  /logout/      →  logout_user()       →  Clear session, redirect to /
GET  /admin/       →  Django admin        →  Browse all StudentRecord entries
```

All URL definitions:
- `mentor/urls.py` — defines the 5 routes above
- `mentorax_ai/urls.py` — includes `mentor/urls.py` under root path `""`

**Why split into two urls.py?**
Django apps are meant to be reusable. Each app owns its URLs.
The project-level urls.py just assembles them together.

---

## 6. Module 1 — Biometric Authorization

**Files involved:** `biometric.html`, `biometric.js`, `views.py` (biometric_scan + authorize)

### What it does
Simulates a fingerprint scan to "authorize" the student before they can use the system.

### How it actually works

1. User visits `/` → Django renders `biometric.html` with an empty `BiometricForm`
2. User types their name and clicks **"Start Scan"**
3. `startScan()` in `biometric.js` runs:
   - Checks name field is not empty (client-side guard)
   - Adds CSS class `scanning` to the fingerprint div → animated scan line starts moving
   - After **1.5 seconds**: updates status text to "Processing..."
   - After **3.0 seconds**: removes `scanning` class, adds `authorized` class (green glow) → submits the HTML form
4. Form POSTs to `/authorize/` → Django's `authorize()` view:
   - Validates `BiometricForm`
   - Saves `authorized = True` and `student_name` to the **session**
   - Redirects to `/input/`

### The fingerprint animation

The fingerprint is just an SVG with 7 concentric ellipses.
The scan line is a `div` with `height: 2px` and a CSS animation (`@keyframes scanMove`)
that moves it from `top: 0` to `top: 100%` in a loop.

```css
/* Scan line sweeps down during scanning */
@keyframes scanMove {
    0%   { top: 0; }
    100% { top: calc(100% - 2px); }
}
```

### Security note
This is a UI simulation. No real biometric hardware or API is connected.
In a real system, you'd integrate with a device SDK (like a fingerprint reader) that
returns a verified match result before setting the session.

---

## 7. Module 2 — Data Acquisition & OCR

**Files involved:** `input.html`, `forms.py (StudentDataForm)`, `views.py (data_input)`

### What it does
Provides the data entry form where a student inputs their academic variables.

### Fields collected

| Field | Type | Validation |
|-------|------|------------|
| Student ID | Text | Required |
| Subject Name | Text | Required |
| Marks Obtained | Float | Required, min=0 |
| Total Marks | Float | Required, min=1 |
| Attendance % | Float | Required, 0–100 |
| Study Hours/Week | Float | Required, min=0 |
| Marksheet Image | File | Optional, DISABLED (OCR placeholder) |

### Custom validation — the important part

Normal Django validation checks each field separately (min/max values).
But we also need a **cross-field rule**: marks cannot be more than total.

This lives in `StudentDataForm.clean()` method in `forms.py`:

```python
def clean(self):
    cleaned_data = super().clean()
    marks = cleaned_data.get("marks_obtained")
    total = cleaned_data.get("total_marks")

    if marks is not None and total is not None:
        if marks > total:
            raise forms.ValidationError(
                f"Marks obtained ({marks}) cannot be greater than total marks ({total})!"
            )
    return cleaned_data
```

`clean()` runs after all individual field validations pass.
If it raises `ValidationError`, the form re-renders with the error shown at the top —
**no data goes to the diagnostic engine if the data is bad.**

### OCR Infrastructure (Placeholder)

The `marksheet_image` field exists in `forms.py` as an `ImageField` but:
- The HTML widget has `disabled="disabled"` attribute
- `required=False` so it never blocks form submission
- A note says "Coming in v2.0"

In a real implementation you'd use a library like `pytesseract` (Python wrapper for
Tesseract OCR) to extract text from the uploaded image and auto-fill the form fields.

---

## 8. Module 3 — Heuristic Diagnostic Engine

**Files involved:** `views.py` — `run_diagnostic_engine()` and `generate_recommendations()`

### What it does
Takes the raw numbers from the form and converts them into meaningful analysis.

### How it's called

Inside `data_input()` view, after the form passes validation:

```python
analysis = run_diagnostic_engine(form.cleaned_data)
```

The result is a dictionary saved to the session and passed to the dashboard template.

### Step-by-step logic

**Step 1 — Performance Percentage**
```
percentage = (marks_obtained / total_marks) × 100
```
Simple formula. Result rounded to 2 decimal places.

**Step 2 — Tier Classification**

| Percentage | Tier | Color |
|------------|------|-------|
| >= 75% | Excellent | Green `#00ff88` |
| 50–74% | Average | Orange `#ffaa00` |
| < 50% | Alert | Red `#ff4444` |

**Step 3 — Correlation Mapping**

The engine checks attendance and study hours independently, then checks cross-patterns:

```
Attendance < 75%       → danger   (likely dragging performance down)
Attendance 75–89%      → info     (satisfactory, can improve)
Attendance >= 90%      → success  (strong positive factor)

Study hours < 7/week   → danger   (way too low)
Study hours 7–19/week  → info     (moderate)
Study hours >= 20/week → success  (high effort)

CROSS: study hours >= 15 AND percentage < 50
  → warning: studying a lot but scoring low = bad study method

CROSS: study hours < 10 AND percentage >= 75
  → info: doing well without much effort = relies on aptitude, risky long-term
```

Each finding is a dictionary with `type`, `icon`, `finding`, and `detail`.
The template loops over these with `{% for item in analysis.correlations %}`.

**Step 4 — Recommendations**

`generate_recommendations()` builds a list of strings based on the tier + habits.
Alert tier gets urgent action items. Excellent tier gets stretch goals. Everyone gets a sleep tip.

**Step 5 — Chart Data Preparation**

Doughnut data (marks obtained vs missed):
```python
doughnut_data = { "obtained": 72, "missed": 28, "total": 100 }
```

Bar chart data (3 metrics normalized to 0–100):
```python
study_hours_normalized = min((study_hours / 30) * 100, 100)
# 30 hrs/week is treated as 100% effort
bar_data = {
    "labels": ["Performance %", "Attendance %", "Study Effort %"],
    "values": [72.0, 78.0, 46.7]
}
```

---

## 9. Module 3b — Groq AI Analysis

**Files involved:** `mentor/groq_service.py`, `.env`, `mentor/views.py`, `dashboard.html`

### What it does

After the heuristic engine runs, the result is passed to Groq's LLM API.
The model (`llama-3.3-70b-versatile`) reads the student's data + heuristic
findings and returns three things:

1. **Personalised Summary** — 2-3 sentence overview of the student's situation
2. **Deep-Dive Recommendations** — 5 specific, actionable suggestions
3. **5-Day Study Plan** — concrete daily tasks tailored to their subject and score

### Setup

1. Get a free API key at `https://console.groq.com/keys`
2. Open `.env` in the project root and set:
   ```
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
   ```
3. Restart the server — AI sections appear automatically on the dashboard.

If the key is missing, the dashboard shows a yellow error card explaining what to do.
All other features (charts, heuristic analysis) still work without the key.

### Model used

`llama-3.3-70b-versatile` — Groq's fastest and most capable free model.
Typical response time: < 2 seconds.

### How it works in code

```python
# mentor/groq_service.py
client = Groq(api_key=api_key)
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[system_msg, user_msg_with_student_data],
    temperature=0.65,
    max_tokens=1024,
)
result = json.loads(response.choices[0].message.content)
```

The system prompt tells the model to respond with raw JSON only.
The user prompt embeds all the student's data + heuristic findings.
The JSON is parsed and added to the `analysis` dict → stored in session → rendered on dashboard.

---

## 10. Module 4 — Neural HUD (Charts)

**Files involved:** `dashboard.html`, Chart.js (loaded from CDN in `base.html`)

### What it does
Renders the analysis visually — charts, metric cards, correlation findings, recommendations.

### How Django passes data to Chart.js

Django is server-side. Chart.js is client-side JavaScript.
They communicate through embedding Django template variables directly into a `<script>` block:

```html
<script>
    const doughnutData = {
        obtained: {{ analysis.doughnut_data.obtained }},   // Django fills this in
        missed:   {{ analysis.doughnut_data.missed }},
    };

    const barData = {
        labels: {{ analysis.bar_data.labels|safe }},  // |safe needed for lists/strings
        values: {{ analysis.bar_data.values|safe }},
    };
</script>
```

When Django renders the HTML, it replaces `{{ ... }}` with real numbers.
The browser then runs the JavaScript with those numbers already baked in.

### Chart 1 — Doughnut (Marks Accuracy)

```javascript
new Chart(ctx, {
    type: "doughnut",
    data: {
        datasets: [{ data: [obtained, missed], ... }]
    },
    options: {
        cutout: "70%",   // hollow center — this is what makes it a doughnut not a pie
    }
});
```

A custom `div` is absolutely positioned in the center of the canvas to show the
percentage text (since Chart.js doesn't have a built-in center label for doughnut).

### Chart 2 — Bar (Multi-metric)

3 bars side by side: Performance %, Attendance %, Study Effort %.
Each bar has its own color (cyan, green, purple).
Y-axis max is always 100 so everything is visually comparable.

### Metric Cards

4 cards across the top of the dashboard showing:
- Performance score (big number, colored per tier)
- Academic tier badge
- Attendance %
- Study hours/week

Color logic uses Django template `{% if %}` tags, not JavaScript.

---

## 10. Database & Model

**File:** `mentor/models.py`

### StudentRecord — the only table in this project

```python
class StudentRecord(models.Model):
    student_name          # CharField  — who submitted
    student_id            # CharField  — their ID (e.g. STU2024001)
    subject_name          # CharField  — which subject this record is for
    marks_obtained        # FloatField — what they scored
    total_marks           # FloatField — out of how much
    attendance_percent    # FloatField — e.g. 78.5
    study_hours_per_week  # FloatField — e.g. 14.0
    performance_percent   # FloatField — calculated and stored (e.g. 72.0)
    tier                  # CharField  — Excellent / Average / Alert
    created_at            # DateTimeField — auto-set to now on save
```

One row = one analysis session.
You can run the analysis multiple times for the same student — each run creates a new row.

### Django ORM — no SQL needed

To save a record:
```python
record = StudentRecord(student_name="Ayush", marks_obtained=72, ...)
record.save()           # Django writes the INSERT SQL for you
```

To query all records:
```python
StudentRecord.objects.all()
StudentRecord.objects.filter(tier="Alert")
StudentRecord.objects.filter(student_id="STU001")
```

### Migrations

Every time you change `models.py`, you must run:
```bash
python manage.py makemigrations   # generates a migration file
python manage.py migrate          # applies it to the database
```

Migrations are versioned files in `mentor/migrations/`.
`0001_initial.py` was auto-generated when we first ran `makemigrations`.

---

## 11. Forms & Validation

**File:** `mentor/forms.py`

### Two forms

**BiometricForm** — just one field:
- `student_name` — CharField, max 100 chars
- Rendered with the CSS class `bio-input` (styled by style.css)

**StudentDataForm** — main data form:
- 6 active fields + 1 disabled OCR field
- Each field has a `widget` that controls what HTML element renders
  (`TextInput`, `NumberInput`, `FileInput`)
- Each field has `attrs` that add HTML attributes like `placeholder`, `class`, `step`

### How Django forms work (short version)

```python
# In the view (data_input):
form = StudentDataForm(request.POST, request.FILES)

if form.is_valid():
    # All fields passed validation AND clean() passed
    data = form.cleaned_data   # dict of validated, type-converted values
    marks = data["marks_obtained"]   # already a Python float, not a string
```

`form.is_valid()` internally:
1. Runs each field's own validation (type check, min/max)
2. Calls `clean_<fieldname>()` methods if they exist
3. Calls `clean()` for cross-field validation
4. Returns `True` only if everything passes

If validation fails, the template re-renders with `{{ form.field.errors }}` showing the messages.

---

## 12. Sessions — How Login State Works

**Django sessions** let you store small amounts of data tied to a browser session.
It works like a server-side dictionary that remembers things between requests.

### How we use it

After biometric authorization (`authorize()` view):
```python
request.session["authorized"] = True
request.session["student_name"] = "Ayush"
```

After analysis runs (`data_input()` view):
```python
request.session["analysis"] = analysis      # dict from diagnostic engine
request.session["marks_obtained"] = 72.0
# ... etc
```

In the dashboard (`dashboard()` view):
```python
analysis = request.session.get("analysis")   # read it back
student_name = request.session.get("student_name")
```

### Session guard (access control)

Every protected view starts with:
```python
if not request.session.get("authorized"):
    return redirect("biometric_scan")
```

If someone tries to visit `/input/` or `/dashboard/` directly without going
through biometric scan first — they get bounced back to `/`.

### Logout

```python
request.session.flush()   # deletes ALL session data for this browser
```

### Where session data is stored

By default Django stores session data in the **database** (`django_session` table).
This is set up automatically by `django.contrib.sessions` in `INSTALLED_APPS` and
`SessionMiddleware` in `MIDDLEWARE` — both already configured in `settings.py`.

---

## 13. Templates & Static Files

### How templates work

All templates extend `base.html` using Django's template inheritance:

```html
<!-- In biometric.html -->
{% extends "base.html" %}

{% block content %}
   <!-- page-specific HTML goes here -->
{% endblock %}
```

`base.html` defines the shell: navbar, flash messages, footer, Chart.js CDN script.
Child templates only fill in their `{% block %}` sections.

**Template tags used:**
| Tag | What it does |
|-----|-------------|
| `{{ variable }}` | Outputs a variable value |
| `{% if %}...{% endif %}` | Conditional rendering |
| `{% for item in list %}` | Loop |
| `{% url 'name' %}` | Generates a URL from its name (avoids hardcoding) |
| `{% static 'path' %}` | Generates the URL to a static file |
| `{% csrf_token %}` | Adds a hidden security token to every POST form |
| `{{ value\|safe }}` | Outputs value without HTML-escaping (used for JS arrays) |

### How static files work

`{% load static %}` at the top of a template enables the `{% static %}` tag.

```html
<link rel="stylesheet" href="{% static 'css/style.css' %}">
<script src="{% static 'js/biometric.js' %}"></script>
```

Django resolves these to `/static/css/style.css` etc. during development.

`settings.py` tells Django where to find static files:
```python
STATICFILES_DIRS = [BASE_DIR / "static"]
```

---

## 14. Admin Panel

Visit `/admin/` (after creating a superuser) to browse all `StudentRecord` entries.

```bash
python manage.py createsuperuser
# Enter username, email, password
```

`mentor/admin.py` registers `StudentRecord` with a custom display:
```python
@admin.register(StudentRecord)
class StudentRecordAdmin(admin.ModelAdmin):
    list_display = ["student_name", "student_id", "subject_name",
                    "performance_percent", "tier", "created_at"]
    list_filter = ["tier"]           # filter sidebar: Excellent / Average / Alert
    search_fields = ["student_name", "student_id"]
```

From admin you can view, edit, delete, or search any record without writing code.

---

## 15. Switch to PostgreSQL

**Short answer: Yes, 100% possible. Zero code changes needed.**

Django's ORM abstracts the database entirely. Your `models.py`, `views.py`, and
all your queries stay exactly the same. Only the `settings.py` connection block changes.

### Why switch?

| SQLite | PostgreSQL |
|--------|------------|
| File-based, zero setup | Requires a running server |
| Good for development | Better for production / multiple users |
| No concurrent writes | Handles concurrent writes properly |
| Included with Python | Needs separate install |

For a college project/demo: **SQLite is fine.**
If you deploy this or want to simulate production: **use PostgreSQL.**

---

### Step-by-step: Switch to PostgreSQL

**Step 1 — Install PostgreSQL**

Download from postgresql.org and install. Remember the password you set for the `postgres` user.

**Step 2 — Create a database for this project**

Open pgAdmin or psql:
```sql
CREATE DATABASE mentorax_db;
CREATE USER mentorax_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE mentorax_db TO mentorax_user;
```

**Step 3 — Install the Python PostgreSQL driver**

```bash
pip install psycopg2-binary
```

`psycopg2` is what Django uses to talk to PostgreSQL. `psycopg2-binary` is
the pre-compiled version — easier to install, no C compiler needed.

**Step 4 — Update settings.py**

Open `mentorax_ai/settings.py` and replace the `DATABASES` block:

```python
# OLD (SQLite):
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# NEW (PostgreSQL):
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "mentorax_db",       # database name you created
        "USER": "mentorax_user",     # your PostgreSQL user
        "PASSWORD": "yourpassword",  # your password
        "HOST": "localhost",         # or "127.0.0.1"
        "PORT": "5432",              # default PostgreSQL port
    }
}
```

**Step 5 — Run migrations on the new database**

```bash
python manage.py migrate
```

Django will create all tables (StudentRecord, sessions, admin, etc.) fresh in PostgreSQL.

**Step 6 — Create superuser again**

The old SQLite data doesn't transfer. You'll need to recreate:
```bash
python manage.py createsuperuser
```

**Step 7 — Run the server normally**

```bash
python manage.py runserver
```

That's it. Everything works exactly the same — the ORM handles the rest.

---

### Optional: Use environment variables for DB credentials

Hardcoding passwords in `settings.py` is bad practice. For a cleaner setup:

```bash
pip install python-dotenv
```

Create a `.env` file in the project root (never commit this to git):
```
DB_NAME=mentorax_db
DB_USER=mentorax_user
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

Update `settings.py`:
```python
from dotenv import load_dotenv
import os

load_dotenv()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     os.getenv("DB_NAME"),
        "USER":     os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST":     os.getenv("DB_HOST", "localhost"),
        "PORT":     os.getenv("DB_PORT", "5432"),
    }
}
```

Add `.env` to your `.gitignore`:
```
.env
db.sqlite3
__pycache__/
*.pyc
```

---

## Quick Reference

```bash
# Run server
python manage.py runserver

# After changing models.py
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Check for config errors
python manage.py check

# Open Django shell (test queries interactively)
python manage.py shell
>>> from mentor.models import StudentRecord
>>> StudentRecord.objects.all()
>>> StudentRecord.objects.filter(tier="Alert")
```

---

*MentoraX AI — Final Year Project — Neural Academic Engine v1.0*
