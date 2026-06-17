import os
import secrets
from datetime import date, datetime
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


SUBJECTS = [
    {
        "id": 1,
        "name": "Mathematics",
        "level": "NECTA / KCSE",
        "materials": 18,
        "tests": 6,
        "description": "Algebra, geometry, probability, and exam-style problem solving.",
    },
    {
        "id": 2,
        "name": "English",
        "level": "NECTA / KCSE",
        "materials": 14,
        "tests": 4,
        "description": "Grammar, comprehension, composition, and literature practice.",
    },
    {
        "id": 3,
        "name": "Biology",
        "level": "NECTA / KCSE",
        "materials": 16,
        "tests": 5,
        "description": "Cell biology, genetics, ecology, human biology, and lab skills.",
    },
    {
        "id": 4,
        "name": "Chemistry",
        "level": "NECTA / KCSE",
        "materials": 12,
        "tests": 5,
        "description": "Atomic structure, bonding, acids, organic chemistry, and calculations.",
    },
]

STUDENT_STATS = {
    "tests_taken": 12,
    "average_score": "78%",
    "materials_read": 34,
    "notifications": 3,
}

RECENT_RESULTS = [
    {"test": "Mathematics Mock 3", "score": "82%", "date": "2026-06-15"},
    {"test": "Biology Paper 2 Drill", "score": "76%", "date": "2026-06-12"},
    {"test": "English Grammar Sprint", "score": "88%", "date": "2026-06-08"},
]

USERS = [
    {"fullname": "Student User", "email": "student@example.com", "role": "Student", "registered": "2026-06-10 14:30"},
    {"fullname": "Admin User", "email": "admin@example.com", "role": "Administrator", "registered": "2026-06-09 09:15"},
]

MATERIALS = [
    {"title": "Mathematics Revision Guide", "subject": "Mathematics", "type": "PDF Notes"},
    {"title": "Biology Model Answers", "subject": "Biology", "type": "Model Answers"},
    {"title": "English Composition Pack", "subject": "English", "type": "Revision Guide"},
    {"title": "Chemistry Practical Notes", "subject": "Chemistry", "type": "PDF Notes"},
]

PAST_PAPERS = [
    {"subject": "Mathematics", "year": 2025, "paper": "Paper 1"},
    {"subject": "Biology", "year": 2024, "paper": "Paper 2"},
    {"subject": "English", "year": 2023, "paper": "Paper 1"},
    {"subject": "Chemistry", "year": 2025, "paper": "Paper 2"},
]

MOCK_TESTS = [
    {"title": "Mathematics Full Mock", "subject": "Mathematics", "duration": 120, "marks": 100, "file_url": "", "file_name": ""},
    {"title": "Biology Topic Test", "subject": "Biology", "duration": 60, "marks": 50, "file_url": "", "file_name": ""},
    {"title": "English Language Mock", "subject": "English", "duration": 90, "marks": 80, "file_url": "", "file_name": ""},
]

NOTIFICATIONS = [
    "New Chemistry practical notes were uploaded.",
    "Mathematics Full Mock is scheduled for Friday.",
    "Your Biology Paper 2 result is ready.",
]


PUBLIC_NAV = [
    ("Home", "home"),
    ("About", "about"),
    ("Subjects", "subjects"),
    ("Contact", "contact"),
]

STUDENT_NAV = [
    ("Dashboard", "student_dashboard"),
    ("Profile", "student_profile"),
    ("Study Materials", "student_materials"),
    ("Past Papers", "student_past_papers"),
    ("Mock Tests", "student_mock_tests"),
    ("Results", "student_results"),
    ("Notifications", "student_notifications"),
]

ADMIN_NAV = [
    ("Dashboard", "admin_dashboard"),
    ("Users", "admin_users"),
    ("Subjects", "admin_subjects"),
    ("Materials", "admin_materials"),
    ("Past Papers", "admin_past_papers"),
    ("Tests", "admin_tests"),
    ("Questions", "admin_questions"),
    ("Reports", "admin_reports"),
]


def normalize_role(role):
    return "admin" if role == "Administrator" else "student"


def dashboard_for_role(role):
    return "admin_dashboard" if role == "admin" else "student_dashboard"


def is_safe_next_path(path):
    return bool(path and path.startswith("/") and not path.startswith("//"))


def default_next_for_endpoint(endpoint):
    return url_for(endpoint) if endpoint else ""


def next_path_for_request():
    next_path = request.args.get("next") or request.form.get("next") or request.path
    return next_path if is_safe_next_path(next_path) else ""


def role_can_open_path(role, path):
    if not path:
        return True
    if path.startswith("/admin"):
        return role == "admin"
    if path.startswith("/student"):
        return role == "student"
    return True


def redirect_after_auth(role):
    next_path = session.pop("auth_next", "")
    if next_path and role_can_open_path(role, next_path):
        return redirect(next_path)
    return redirect(url_for(dashboard_for_role(role)))


def delete_by_index(items, item_id):
    index = item_id - 1
    if 0 <= index < len(items):
        items.pop(index)


def delete_by_id(items, item_id):
    for index, item in enumerate(items):
        if item.get("id") == item_id:
            items.pop(index)
            break


def form_int(name, default=0):
    try:
        return int(request.form.get(name, default))
    except (TypeError, ValueError):
        return default


def format_elapsed_time(total_seconds):
    total_seconds = max(0, int(total_seconds or 0))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def save_uploaded_file(field_name):
    uploaded_file = request.files.get(field_name)
    if not uploaded_file or not uploaded_file.filename:
        return ""
    filename = f"{secrets.token_hex(6)}-{secure_filename(uploaded_file.filename)}"
    uploaded_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return url_for("static", filename=f"uploads/{filename}")


def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            user_role = session.get("user_role")
            if not user_role:
                session["auth_next"] = next_path_for_request()
                return redirect(url_for("register", next=session["auth_next"]))
            if role and user_role != role:
                return redirect(url_for(dashboard_for_role(user_role)))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


@app.context_processor
def inject_navigation():
    current_user_name = session.get("user_name", "Student User")
    current_user_initials = "".join(part[:1] for part in current_user_name.split()[:2]).upper() or "SU"
    return {
        "public_nav": PUBLIC_NAV,
        "student_nav": STUDENT_NAV,
        "admin_nav": ADMIN_NAV,
        "current_user_role": session.get("user_role"),
        "current_user_name": current_user_name,
        "current_user_initials": current_user_initials,
        "current_dashboard_endpoint": dashboard_for_role(session.get("user_role", "student")),
    }


@app.route("/")
def home():
    return render_template(
        "home.html",
        title="Home",
        subjects=SUBJECTS,
        stats={"students": "2,400+", "papers": "850+", "tests": "120+", "pass_rate": "91%"},
    )


@app.route("/about")
def about():
    return render_template("about.html", title="About Us")


@app.route("/subjects")
def subjects():
    return render_template("subjects.html", title="Subjects", subjects=SUBJECTS)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    submitted = request.method == "POST"
    return render_template("contact.html", title="Contact Us", submitted=submitted)


@app.route("/login", methods=["GET", "POST"])
def login():
    next_path = request.values.get("next") or session.get("auth_next") or ""
    if is_safe_next_path(next_path):
        session["auth_next"] = next_path

    if request.method == "POST":
        role = request.form.get("role") or session.get("pending_login_role") or "student"
        user_role = normalize_role(role)
        email = request.form.get("email") or session.get("pending_login_email", "")
        user = next((user for user in USERS if user["email"] == email), None)
        session["user_role"] = user_role
        session["user_name"] = session.get("pending_login_name") or (user["fullname"] if user else "Student User")
        session["user_email"] = email
        session.pop("pending_login_role", None)
        session.pop("pending_login_email", None)
        session.pop("pending_login_name", None)
        return redirect_after_auth(user_role)

    registered = request.args.get("registered") == "1"
    return render_template(
        "login.html",
        title="Login",
        registered=registered,
        pending_role=session.get("pending_login_role", "student"),
        pending_email=session.get("pending_login_email", ""),
        next_path=session.get("auth_next", ""),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    next_path = request.values.get("next") or session.get("auth_next") or ""
    if is_safe_next_path(next_path):
        session["auth_next"] = next_path

    if request.method == "POST":
        fullname = request.form.get("fullname", "Student User").strip() or "Student User"
        email = request.form.get("email", "")
        role = request.form.get("role", "Student")
        USERS.append({"fullname": fullname, "email": email, "role": role, "registered": datetime.now().strftime("%Y-%m-%d %H:%M")})
        session["pending_login_role"] = normalize_role(role)
        session["pending_login_email"] = email
        session["pending_login_name"] = fullname
        return redirect(url_for("login", registered=1))

    return render_template("register.html", title="Register", next_path=session.get("auth_next", ""))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/student/dashboard")
@login_required("student")
def student_dashboard():
    return render_template(
        "student/dashboard.html",
        title="Student Dashboard",
        stats=STUDENT_STATS,
        recent_results=RECENT_RESULTS,
        materials=MATERIALS[:3],
    )


@app.route("/student/profile", methods=["GET", "POST"])
@login_required("student")
def student_profile():
    submitted = request.method == "POST"
    return render_template("student/profile.html", title="Profile", submitted=submitted)


@app.route("/student/materials")
@login_required("student")
def student_materials():
    return render_template("student/materials.html", title="Study Materials", materials=MATERIALS)


@app.route("/student/past-papers")
@login_required("student")
def student_past_papers():
    return render_template("student/past_papers.html", title="Past Papers", papers=PAST_PAPERS)


@app.route("/student/mock-tests")
@login_required("student")
def student_mock_tests():
    return render_template("student/mock_tests.html", title="Mock Tests", tests=MOCK_TESTS)


@app.route("/student/mock-tests/<int:test_id>")
@login_required("student")
def student_take_test(test_id):
    test = MOCK_TESTS[test_id - 1] if 0 < test_id <= len(MOCK_TESTS) else MOCK_TESTS[0]
    return render_template("student/take_test.html", title="Take Mock Test", test=test, test_id=test_id)


@app.route("/student/mock-tests/<int:test_id>/submit", methods=["POST"])
@login_required("student")
def student_submit_test(test_id):
    test = MOCK_TESTS[test_id - 1] if 0 < test_id <= len(MOCK_TESTS) else MOCK_TESTS[0]
    elapsed_seconds = form_int("elapsed_seconds")
    RECENT_RESULTS.insert(
        0,
        {
            "test": test["title"],
            "score": "Submitted",
            "date": date.today().isoformat(),
            "time_spent": format_elapsed_time(elapsed_seconds),
        },
    )
    return redirect(url_for("student_results"))


@app.route("/student/results")
@login_required("student")
def student_results():
    return render_template("student/results.html", title="Results", results=RECENT_RESULTS)


@app.route("/student/notifications")
@login_required("student")
def student_notifications():
    return render_template(
        "student/notifications.html",
        title="Notifications",
        notifications=NOTIFICATIONS,
    )


@app.route("/admin/dashboard")
@login_required("admin")
def admin_dashboard():
    return render_template("admin/dashboard.html", title="Admin Dashboard")


@app.route("/admin/users")
@login_required("admin")
def admin_users():
    return render_template("admin/users.html", title="Manage Users", users=USERS)


@app.route("/admin/users/new", methods=["GET", "POST"])
@login_required("admin")
def admin_user_form():
    if request.method == "POST":
        USERS.append(
            {
                "fullname": request.form.get("fullname", "New User"),
                "email": request.form.get("email", ""),
                "role": request.form.get("role", "Student"),
            }
        )
        return redirect(url_for("admin_users"))

    return render_template(
        "admin/form.html",
        title="Add User",
        submitted=False,
        return_endpoint="admin_users",
        fields=[
            {"label": "Full name", "name": "fullname", "type": "text"},
            {"label": "Email", "name": "email", "type": "email"},
            {"label": "Role", "name": "role", "type": "select", "options": ["Student", "Administrator"]},
        ],
    )


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required("admin")
def admin_delete_user(user_id):
    delete_by_index(USERS, user_id)
    return redirect(url_for("admin_users"))


@app.route("/admin/subjects")
@login_required("admin")
def admin_subjects():
    return render_template("admin/subjects.html", title="Manage Subjects", subjects=SUBJECTS)


@app.route("/admin/subjects/<int:subject_id>/delete", methods=["POST"])
@login_required("admin")
def admin_delete_subject(subject_id):
    delete_by_id(SUBJECTS, subject_id)
    return redirect(url_for("admin_subjects"))


@app.route("/admin/subjects/<int:subject_id>/edit", methods=["GET", "POST"])
@login_required("admin")
def admin_subject_edit(subject_id):
    subject = next((s for s in SUBJECTS if s["id"] == subject_id), None)
    if not subject:
        return redirect(url_for("admin_subjects"))

    if request.method == "POST":
        subject["name"] = request.form.get("subject_name", subject["name"])
        subject["level"] = request.form.get("level", subject["level"])
        subject["description"] = request.form.get("description", subject["description"])
        return redirect(url_for("admin_subjects"))

    return render_template(
        "admin/form.html",
        title="Edit Subject",
        submitted=True,
        return_endpoint="admin_subjects",
        fields=[
            {"label": "Subject name", "name": "subject_name", "type": "text", "value": subject["name"]},
            {"label": "Level", "name": "level", "type": "text", "value": subject["level"]},
            {"label": "Description", "name": "description", "type": "textarea", "value": subject["description"]},
        ],
    )


@app.route("/admin/subjects/new", methods=["GET", "POST"])
@login_required("admin")
def admin_subject_form():
    if request.method == "POST":
        next_id = max((s.get("id", 0) for s in SUBJECTS), default=0) + 1
        SUBJECTS.append(
            {
                "id": next_id,
                "name": request.form.get("subject_name", "New Subject"),
                "level": request.form.get("level", ""),
                "materials": 0,
                "tests": 0,
                "description": request.form.get("description", ""),
            }
        )
        return redirect(url_for("admin_subjects"))

    return render_template(
        "admin/form.html",
        title="Add Subject",
        submitted=False,
        return_endpoint="admin_subjects",
        fields=[
            {"label": "Subject name", "name": "subject_name", "type": "text"},
            {"label": "Level", "name": "level", "type": "text"},
            {"label": "Description", "name": "description", "type": "textarea"},
        ],
    )


@app.route("/admin/materials")
@login_required("admin")
def admin_materials():
    return render_template("admin/materials.html", title="Manage Materials", materials=MATERIALS)


@app.route("/admin/materials/new", methods=["GET", "POST"])
@login_required("admin")
def admin_material_form():
    if request.method == "POST":
        MATERIALS.append(
            {
                "title": request.form.get("title", "New Material"),
                "subject": request.form.get("subject", ""),
                "type": request.form.get("type", "PDF Notes"),
                "file_url": save_uploaded_file("upload_file"),
                "source_url": request.form.get("source_url", "").strip(),
            }
        )
        return redirect(url_for("admin_materials"))

    return render_template(
        "admin/form.html",
        title="Upload Material",
        submitted=False,
        has_upload=True,
        return_endpoint="admin_materials",
        fields=[
            {"label": "Title", "name": "title", "type": "text"},
            {"label": "Subject", "name": "subject", "type": "select", "options": [subject["name"] for subject in SUBJECTS]},
            {"label": "Material type", "name": "type", "type": "select", "options": ["PDF Notes", "Revision Guide", "Model Answers"]},
            {"label": "Upload file", "name": "upload_file", "type": "file", "accept": ".pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png"},
            {"label": "External URL", "name": "source_url", "type": "url"},
        ],
    )


@app.route("/admin/materials/<int:material_id>/delete", methods=["POST"])
@login_required("admin")
def admin_delete_material(material_id):
    delete_by_index(MATERIALS, material_id)
    return redirect(url_for("admin_materials"))


@app.route("/admin/past-papers")
@login_required("admin")
def admin_past_papers():
    return render_template("admin/past_papers.html", title="Manage Past Papers", papers=PAST_PAPERS)


@app.route("/admin/past-papers/new", methods=["GET", "POST"])
@login_required("admin")
def admin_paper_form():
    if request.method == "POST":
        PAST_PAPERS.append(
            {
                "subject": request.form.get("subject", ""),
                "year": form_int("year", date.today().year),
                "paper": request.form.get("paper", "Paper"),
                "file_url": save_uploaded_file("upload_file"),
                "source_url": request.form.get("source_url", "").strip(),
            }
        )
        return redirect(url_for("admin_past_papers"))

    return render_template(
        "admin/form.html",
        title="Upload Past Paper",
        submitted=False,
        has_upload=True,
        return_endpoint="admin_past_papers",
        fields=[
            {"label": "Subject", "name": "subject", "type": "select", "options": [subject["name"] for subject in SUBJECTS]},
            {"label": "Year", "name": "year", "type": "number"},
            {"label": "Paper", "name": "paper", "type": "text"},
            {"label": "Upload file", "name": "upload_file", "type": "file", "accept": ".pdf,.doc,.docx,.jpg,.jpeg,.png"},
            {"label": "External URL", "name": "source_url", "type": "url"},
        ],
    )


@app.route("/admin/past-papers/<int:paper_id>/delete", methods=["POST"])
@login_required("admin")
def admin_delete_paper(paper_id):
    delete_by_index(PAST_PAPERS, paper_id)
    return redirect(url_for("admin_past_papers"))


@app.route("/admin/tests")
@login_required("admin")
def admin_tests():
    return render_template("admin/tests.html", title="Manage Tests", tests=MOCK_TESTS)


@app.route("/admin/tests/new", methods=["GET", "POST"])
@login_required("admin")
def admin_test_form():
    if request.method == "POST":
        MOCK_TESTS.append(
            {
                "title": request.form.get("title", "New Test"),
                "subject": request.form.get("subject", ""),
                "duration": form_int("duration", 60),
                "marks": form_int("total_marks", 100),
                "questions": [],
                "file_url": save_uploaded_file("upload_file"),
                "file_name": request.files.get("upload_file").filename if request.files.get("upload_file") and request.files.get("upload_file").filename else "",
            }
        )
        return redirect(url_for("admin_tests"))

    return render_template(
        "admin/form.html",
        title="Create Test",
        submitted=False,
        has_upload=True,
        return_endpoint="admin_tests",
        fields=[
            {"label": "Test title", "name": "title", "type": "text"},
            {"label": "Subject", "name": "subject", "type": "select", "options": [subject["name"] for subject in SUBJECTS]},
            {"label": "Duration minutes", "name": "duration", "type": "number"},
            {"label": "Total marks", "name": "total_marks", "type": "number"},
            {"label": "Upload test file", "name": "upload_file", "type": "file", "accept": ".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"},
        ],
    )


@app.route("/admin/tests/<int:test_id>/delete", methods=["POST"])
@login_required("admin")
def admin_delete_test(test_id):
    delete_by_index(MOCK_TESTS, test_id)
    return redirect(url_for("admin_tests"))


@app.route("/admin/tests/upload-external", methods=["GET", "POST"])
@login_required("admin")
def admin_test_upload_external():
    if request.method == "POST":
        uploaded_file_url = save_uploaded_file("upload_file")
        MOCK_TESTS.append(
            {
                "title": request.form.get("title", "External Test"),
                "subject": request.form.get("subject", ""),
                "duration": form_int("duration", 60),
                "marks": form_int("total_marks", 100),
                "questions": [],
                "file_url": uploaded_file_url,
                "file_name": request.files.get("upload_file").filename if request.files.get("upload_file") and request.files.get("upload_file").filename else "",
            }
        )
        return redirect(url_for("admin_tests"))

    return render_template(
        "admin/form.html",
        title="Upload External Test",
        submitted=False,
        has_upload=True,
        return_endpoint="admin_tests",
        fields=[
            {"label": "Test title", "name": "title", "type": "text"},
            {"label": "Subject", "name": "subject", "type": "select", "options": [subject["name"] for subject in SUBJECTS]},
            {"label": "Duration minutes", "name": "duration", "type": "number"},
            {"label": "Total marks", "name": "total_marks", "type": "number"},
            {"label": "Upload test file", "name": "upload_file", "type": "file", "accept": ".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"},
        ],
    )


@app.route("/admin/questions")
@login_required("admin")
def admin_questions():
    return render_template("admin/questions.html", title="Manage Questions", tests=MOCK_TESTS)


@app.route("/admin/questions/new", methods=["GET", "POST"])
@login_required("admin")
def admin_question_form():
    if request.method == "POST":
        selected_title = request.form.get("test")
        question = {
            "text": request.form.get("question", "New question"),
            "answer": request.form.get("correct_answer", "A"),
            "marks": form_int("marks", 1),
            "options": ["Option A", "Option B", "Option C", "Option D"],
        }
        for test in MOCK_TESTS:
            if test["title"] == selected_title:
                test.setdefault("questions", []).append(question)
                break
        return redirect(url_for("admin_questions"))

    return render_template(
        "admin/form.html",
        title="Add Question",
        submitted=False,
        return_endpoint="admin_questions",
        fields=[
            {"label": "Test", "name": "test", "type": "select", "options": [test["title"] for test in MOCK_TESTS]},
            {"label": "Question", "name": "question", "type": "textarea"},
            {"label": "Correct answer", "name": "correct_answer", "type": "select", "options": ["A", "B", "C", "D"]},
            {"label": "Marks", "name": "marks", "type": "number"},
        ],
    )


@app.route("/admin/reports")
@login_required("admin")
def admin_reports():
    return render_template("admin/reports.html", title="Reports", results=RECENT_RESULTS)


@app.route("/health/routes")
def route_health():
    routes = [
        {
            "endpoint": rule.endpoint,
            "path": rule.rule,
            "url": url_for(rule.endpoint, **{argument: 1 for argument in rule.arguments}),
        }
        for rule in app.url_map.iter_rules()
        if rule.endpoint != "static"
    ]
    return {"routes": routes}


if __name__ == "__main__":
    app.run(debug=True)
