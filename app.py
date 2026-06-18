import os
import secrets
import sqlite3
import json
from datetime import date, datetime, timedelta
from flask import Response
import queue
import threading
from functools import wraps

from flask import Flask, g, redirect, render_template, request, session, url_for, jsonify
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")

# Notification system for live updates
notification_queue = queue.Queue()
app.config["DATABASE"] = os.environ.get("DATABASE") or os.path.join(app.instance_path, "examprep.sqlite3")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.instance_path, exist_ok=True)


SUBJECTS = [
    {
        "id": 1,
        "name": "Mathematics",
        "level": "NECTA / KCSE",
        "materials": 5,
        "tests": 6,
        "description": "Algebra, geometry, probability, and exam-style problem solving.",
    },
    {
        "id": 2,
        "name": "English",
        "level": "NECTA / KCSE",
        "materials": 2,
        "tests": 4,
        "description": "Grammar, comprehension, composition, and literature practice.",
    },
    {
        "id": 3,
        "name": "Biology",
        "level": "NECTA / KCSE",
        "materials": 4,
        "tests": 5,
        "description": "Cell biology, genetics, ecology, human biology, and lab skills.",
    },
    {
        "id": 4,
        "name": "Chemistry",
        "level": "NECTA / KCSE",
        "materials": 4,
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
    {"id": 1, "fullname": "Admin User", "email": "admin@gmail.com", "role": "Administrator", "registered": "2026-06-09 09:15"},
]

MATERIALS = [
    {
        "title": "Basic Mathematics Syllabus F1-F4 (2017)",
        "subject": "Mathematics",
        "type": "Syllabus",
        "source_url": "https://maktaba.tetea.org/study-aids/o-level/syllabi/Syllabus - Basic Math - F1-F4 - 2017.pdf",
    },
    {
        "title": "Shika na Mikono - Mathematics",
        "subject": "Mathematics",
        "type": "PDF Notes",
        "source_url": "https://maktaba.tetea.org/study-aids/Shika na Mikono - Math v3-0.pdf",
    },
    {
        "title": "The Circle and Theorems",
        "subject": "Mathematics",
        "type": "PDF Notes",
        "source_url": "https://maktaba.tetea.org/study-aids/o-level/math/TheCircle-F3-Loibanguti(2022).pdf",
    },
    {
        "title": "The Earth as a Sphere",
        "subject": "Mathematics",
        "type": "PDF Notes",
        "source_url": "https://maktaba.tetea.org/study-aids/o-level/math/TheEarthAsASphere-F3-Loibanguti(2022).pdf",
    },
    {
        "title": "Advanced Mathematics Syllabus F5-F6 (2017)",
        "subject": "Mathematics",
        "type": "Syllabus",
        "source_url": "https://maktaba.tetea.org/study-aids/a-level/syllabi/Syllabus - Advanced Math - F5-F6 - 2017.pdf",
    },
    {
        "title": "Biology Syllabus F1-F4 (2012)",
        "subject": "Biology",
        "type": "Syllabus",
        "source_url": "https://maktaba.tetea.org/study-aids/o-level/syllabi/Syllabus - Biology - F1-F4 - 2012.pdf",
    },
    {
        "title": "Biology Study Guide",
        "subject": "Biology",
        "type": "Revision Guide",
        "source_url": "https://maktaba.tetea.org/study-aids/Abbey Secondary School Study Guides Final Biology.pdf",
    },
    {
        "title": "Biology Practical Exam Guidelines",
        "subject": "Biology",
        "type": "PDF Notes",
        "source_url": "https://maktaba.tetea.org/study-aids/practicals/Biology-PracticalGuidelines-2021.pdf",
    },
    {
        "title": "Shika na Mikono - Biology",
        "subject": "Biology",
        "type": "PDF Notes",
        "source_url": "https://maktaba.tetea.org/study-aids/Shika na Mikono - Biology v2-0.pdf",
    },
    {
        "title": "Chemistry Syllabus F1-F4 (2017)",
        "subject": "Chemistry",
        "type": "Syllabus",
        "source_url": "https://maktaba.tetea.org/study-aids/o-level/syllabi/Syllabus-Chemistry-F1-F4-2017.pdf",
    },
    {
        "title": "Chemistry Study Guide",
        "subject": "Chemistry",
        "type": "Revision Guide",
        "source_url": "https://maktaba.tetea.org/study-aids/Abbey Secondary School Study Guides Final Chemistry.pdf",
    },
    {
        "title": "Chemistry Practical Exam Guidelines",
        "subject": "Chemistry",
        "type": "PDF Notes",
        "source_url": "https://maktaba.tetea.org/study-aids/practicals/Chemistry-PracticalGuidelines-2021.pdf",
    },
    {
        "title": "Shika na Mikono - Chemistry",
        "subject": "Chemistry",
        "type": "PDF Notes",
        "source_url": "https://maktaba.tetea.org/study-aids/Shika na Mikono - Chemistry v2-0.pdf",
    },
    {
        "title": "English Syllabus F1-F4 (2016)",
        "subject": "English",
        "type": "Syllabus",
        "source_url": "https://maktaba.tetea.org/study-aids/o-level/syllabi/Syllabus - English - F1-F4 - 2016.pdf",
    },
    {
        "title": "English Syllabus F5-F6 (2017)",
        "subject": "English",
        "type": "Syllabus",
        "source_url": "https://maktaba.tetea.org/study-aids/a-level/syllabi/Syllabus - English - F5-F6 - 2017.pdf",
    },
]

PAST_PAPERS = [
    {
        "subject": "Mathematics",
        "year": 2025,
        "paper": "CSEE Basic Mathematics",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/basic_math/BasicMath-F4-2025.pdf",
    },
    {
        "subject": "Mathematics",
        "year": 2024,
        "paper": "CSEE Basic Mathematics",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/basic_math/BasicMath-F4-2024.pdf",
    },
    {
        "subject": "Mathematics",
        "year": 2024,
        "paper": "CSEE Basic Mathematics Solutions",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/basic_math/BasicMath-F4-2024-Solutions.pdf",
    },
    {
        "subject": "Mathematics",
        "year": 2025,
        "paper": "ACSEE Advanced Mathematics Paper 1",
        "source_url": "https://maktaba.tetea.org/past-papers/acsee/adv_math/AdvancedMath1-F6-2025.pdf",
    },
    {
        "subject": "Biology",
        "year": 2025,
        "paper": "CSEE Biology Paper 1",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/biology/Biology1-F4-2025.pdf",
    },
    {
        "subject": "Biology",
        "year": 2025,
        "paper": "CSEE Biology Paper 1 Solutions",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/biology/Biology1-F4-2025-Solutions.pdf",
    },
    {
        "subject": "Biology",
        "year": 2024,
        "paper": "CSEE Biology Paper 1",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/biology/Biology1-F4-2024.pdf",
    },
    {
        "subject": "Biology",
        "year": 2025,
        "paper": "ACSEE Biology Paper 1",
        "source_url": "https://maktaba.tetea.org/past-papers/acsee/biology/Biology1-F6-2025.pdf",
    },
    {
        "subject": "Chemistry",
        "year": 2025,
        "paper": "CSEE Chemistry Paper 1",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/chemistry/Chemistry1-F4-2025.pdf",
    },
    {
        "subject": "Chemistry",
        "year": 2025,
        "paper": "CSEE Chemistry Paper 1 Solutions",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/chemistry/Chemistry1-F4-2025-Solutions.pdf",
    },
    {
        "subject": "Chemistry",
        "year": 2024,
        "paper": "CSEE Chemistry Paper 1",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/chemistry/Chemistry1-F4-2024.pdf",
    },
    {
        "subject": "Chemistry",
        "year": 2025,
        "paper": "ACSEE Chemistry Paper 1",
        "source_url": "https://maktaba.tetea.org/past-papers/acsee/chemistry/Chemistry1-F6-2025.pdf",
    },
    {
        "subject": "English",
        "year": 2025,
        "paper": "CSEE English Language",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/english/English-F4-2025.pdf",
    },
    {
        "subject": "English",
        "year": 2025,
        "paper": "CSEE English Language Solutions",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/english/English-F4-2025-Solutions.pdf",
    },
    {
        "subject": "English",
        "year": 2024,
        "paper": "CSEE English Language",
        "source_url": "https://maktaba.tetea.org/past-papers/csee/english/English-F4-2024.pdf",
    },
    {
        "subject": "English",
        "year": 2025,
        "paper": "ACSEE English Language Paper 1",
        "source_url": "https://maktaba.tetea.org/past-papers/acsee/english/EnglishLanguage1-F6-2025.pdf",
    },
]

MOCK_TESTS = [
    {
        "title": "Mathematics Full Mock",
        "subject": "Mathematics",
        "duration": 120,
        "marks": 10,
        "questions": [
            {
                "text": "What is the value of x in the equation 3x - 7 = 8?",
                "answer": "B",
                "marks": 5,
                "options": ["x = 3", "x = 5", "x = 7", "x = 9"]
            },
            {
                "text": "What is the derivative of x^2 with respect to x?",
                "answer": "A",
                "marks": 5,
                "options": ["2x", "x", "2", "x^2"]
            }
        ],
        "file_url": "",
        "file_name": ""
    },
    {
        "title": "Biology Topic Test",
        "subject": "Biology",
        "duration": 60,
        "marks": 10,
        "questions": [
            {
                "text": "Which organelle is known as the powerhouse of the cell?",
                "answer": "C",
                "marks": 5,
                "options": ["Nucleus", "Ribosome", "Mitochondria", "Golgi apparatus"]
            },
            {
                "text": "What is the primary site of photosynthesis in plants?",
                "answer": "B",
                "marks": 5,
                "options": ["Stem", "Leaf", "Root", "Flower"]
            }
        ],
        "file_url": "",
        "file_name": ""
    },
    {
        "title": "English Language Mock",
        "subject": "English",
        "duration": 90,
        "marks": 10,
        "questions": [
            {
                "text": "Choose the synonym of 'benevolent'.",
                "answer": "A",
                "marks": 5,
                "options": ["Kind", "Malevolent", "Cruel", "Selfish"]
            },
            {
                "text": "Identify the conjunction in: 'I wanted to go, but it started raining.'",
                "answer": "D",
                "marks": 5,
                "options": ["wanted", "to", "raining", "but"]
            }
        ],
        "file_url": "",
        "file_name": ""
    },
]

NOTIFICATIONS = [
    "New Chemistry practical notes were uploaded.",
    "Mathematics Full Mock is scheduled for Friday.",
    "Your Biology Paper 2 result is ready.",
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def db_execute(sql, params=()):
    db = get_db()
    cursor = db.execute(sql, params)
    db.commit()
    return cursor


def db_all(sql, params=()):
    return get_db().execute(sql, params).fetchall()


def db_one(sql, params=()):
    return get_db().execute(sql, params).fetchone()


def normalize_date(value):
    if isinstance(value, date):
        return value.isoformat()
    return value or date.today().isoformat()


class DbRecord(dict):
    def __init__(self, collection, data):
        super().__init__(data)
        self.collection = collection

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.collection.update_field(self["id"], key, value)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc


class DbCollection:
    def __init__(self, table, columns, order_by="id ASC"):
        self.table = table
        self.columns = columns
        self.order_by = order_by

    def _record_from_row(self, row):
        return DbRecord(self, dict(row))

    def _rows(self):
        return db_all(f"SELECT * FROM {self.table} ORDER BY {self.order_by}")

    def __iter__(self):
        return (self._record_from_row(row) for row in self._rows())

    def __len__(self):
        return db_one(f"SELECT COUNT(*) AS total FROM {self.table}")["total"]

    def __getitem__(self, key):
        rows = self._rows()
        if isinstance(key, slice):
            return [self._record_from_row(row) for row in rows[key]]
        return self._record_from_row(rows[key])

    def get(self, item_id):
        row = db_one(f"SELECT * FROM {self.table} WHERE id = ?", (item_id,))
        return self._record_from_row(row) if row else None

    def append(self, item):
        fields = [column for column in self.columns if column in item]
        placeholders = ", ".join("?" for _ in fields)
        db_execute(
            f"INSERT INTO {self.table} ({', '.join(fields)}) VALUES ({placeholders})",
            tuple(item.get(field) for field in fields),
        )

    def insert(self, index, item):
        self.append(item)

    def pop(self, index=-1):
        item = self[index]
        db_execute(f"DELETE FROM {self.table} WHERE id = ?", (item["id"],))
        return item

    def update_field(self, item_id, key, value):
        if key in self.columns:
            db_execute(f"UPDATE {self.table} SET {key} = ? WHERE id = ?", (value, item_id))


class TestRecord(DbRecord):
    def __init__(self, collection, data):
        super().__init__(collection, data)
        dict.__setitem__(self, "questions", QuestionCollection(data["id"]))


class TestCollection(DbCollection):
    def __init__(self):
        super().__init__("tests", ["title", "subject", "duration", "marks", "file_url", "file_name"])

    def _record_from_row(self, row):
        return TestRecord(self, dict(row))

    def append(self, item):
        cursor = db_execute(
            """
            INSERT INTO tests (title, subject, duration, marks, file_url, file_name)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("title", "New Test"),
                item.get("subject", ""),
                item.get("duration", 60),
                item.get("marks", 100),
                item.get("file_url", ""),
                item.get("file_name", ""),
            ),
        )
        test_id = cursor.lastrowid
        for question in item.get("questions", []):
            QuestionCollection(test_id).append(question)


class QuestionCollection:
    def __init__(self, test_id):
        self.test_id = test_id

    def _rows(self):
        return db_all("SELECT * FROM questions WHERE test_id = ? ORDER BY id ASC", (self.test_id,))

    def _record_from_row(self, row):
        data = dict(row)
        data["options"] = json.loads(data.get("options_json") or "[]")
        data.pop("options_json", None)
        return DbRecord(self, data)

    def __iter__(self):
        return (self._record_from_row(row) for row in self._rows())

    def __len__(self):
        return db_one("SELECT COUNT(*) AS total FROM questions WHERE test_id = ?", (self.test_id,))["total"]

    def __getitem__(self, key):
        rows = self._rows()
        if isinstance(key, slice):
            return [self._record_from_row(row) for row in rows[key]]
        return self._record_from_row(rows[key])

    def get(self, item_id):
        row = db_one("SELECT * FROM questions WHERE test_id = ? AND id = ?", (self.test_id, item_id))
        return self._record_from_row(row) if row else None

    def __setitem__(self, key, item):
        current = self[key]
        self.replace(current["id"], item)

    def replace(self, item_id, item):
        db_execute(
            """
            UPDATE questions
            SET test_id = ?, text = ?, answer = ?, marks = ?, remark = ?, options_json = ?
            WHERE id = ?
            """,
            (
                self.test_id,
                item.get("text", "New question"),
                item.get("answer", "A"),
                item.get("marks", 1),
                item.get("remark", ""),
                json.dumps(item.get("options", [])),
                item_id,
            ),
        )

    def append(self, item):
        db_execute(
            """
            INSERT INTO questions (test_id, text, answer, marks, remark, options_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self.test_id,
                item.get("text", "New question"),
                item.get("answer", "A"),
                item.get("marks", 1),
                item.get("remark", ""),
                json.dumps(item.get("options", [])),
            ),
        )

    def pop(self, index=-1):
        item = self[index]
        self.delete(item["id"])
        return item

    def delete(self, item_id):
        db_execute("DELETE FROM questions WHERE id = ?", (item_id,))

    def update_field(self, item_id, key, value):
        if key == "options":
            key = "options_json"
            value = json.dumps(value)
        if key in {"test_id", "text", "answer", "marks", "remark", "options_json"}:
            db_execute(f"UPDATE questions SET {key} = ? WHERE id = ?", (value, item_id))


class ExamAttemptCollection(DbCollection):
    def __init__(self):
        super().__init__("exam_attempts", ["user_id", "test_id", "start_time", "end_time", "submitted_time", "status", "created_at"], "id DESC")

    def append(self, item):
        cursor = db_execute(
            """
            INSERT INTO exam_attempts (user_id, test_id, start_time, end_time, submitted_time, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("user_id", 1),
                item.get("test_id"),
                item.get("start_time"),
                item.get("end_time"),
                item.get("submitted_time"),
                item.get("status", "ACTIVE"),
                item.get("created_at", datetime.now().isoformat()),
            ),
        )
        return cursor.lastrowid

    def start_exam(self, user_id, test_id, duration_minutes):
        """Create a new exam attempt with calculated end time"""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        attempt_id = self.append({
            "user_id": user_id,
            "test_id": test_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "submitted_time": None,
            "status": "ACTIVE",
            "created_at": start_time.isoformat(),
        })
        return attempt_id

    def get_active_attempt(self, user_id, test_id):
        """Get the active exam attempt for a user and test"""
        row = db_one(
            """
            SELECT * FROM exam_attempts 
            WHERE user_id = ? AND test_id = ? AND status = 'ACTIVE'
            ORDER BY id DESC LIMIT 1
            """,
            (user_id, test_id)
        )
        return self._record_from_row(row) if row else None

    def get_attempt_status(self, attempt_id):
        """Get current status and remaining time for an attempt"""
        row = db_one("SELECT * FROM exam_attempts WHERE id = ?", (attempt_id,))
        if not row:
            return None
        
        attempt = self._record_from_row(row)
        end_time = datetime.fromisoformat(attempt["end_time"])
        current_time = datetime.now()
        
        if current_time >= end_time:
            # Time expired
            remaining_seconds = 0
            status = "EXPIRED"
        else:
            remaining_seconds = int((end_time - current_time).total_seconds())
            status = attempt["status"]
        
        return {
            "id": attempt["id"],
            "status": status,
            "remaining_seconds": remaining_seconds,
            "end_time": attempt["end_time"],
            "start_time": attempt["start_time"],
            "current_server_time": current_time.isoformat(),
        }

    def submit_attempt(self, attempt_id):
        """Mark an attempt as submitted"""
        db_execute(
            "UPDATE exam_attempts SET status = 'SUBMITTED', submitted_time = ? WHERE id = ?",
            (datetime.now().isoformat(), attempt_id)
        )


def create_schema():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level TEXT DEFAULT '',
            materials INTEGER DEFAULT 0,
            tests INTEGER DEFAULT 0,
            description TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL,
            registered TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT DEFAULT '',
            type TEXT DEFAULT '',
            file_url TEXT DEFAULT '',
            source_url TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS past_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT DEFAULT '',
            year INTEGER DEFAULT 0,
            paper TEXT DEFAULT '',
            file_url TEXT DEFAULT '',
            source_url TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT DEFAULT '',
            duration INTEGER DEFAULT 60,
            marks INTEGER DEFAULT 100,
            file_url TEXT DEFAULT '',
            file_name TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            answer TEXT DEFAULT 'A',
            marks INTEGER DEFAULT 1,
            remark TEXT DEFAULT '',
            options_json TEXT DEFAULT '[]',
            FOREIGN KEY (test_id) REFERENCES tests (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT DEFAULT '',
            subject TEXT DEFAULT '',
            test TEXT NOT NULL,
            score TEXT DEFAULT '',
            date TEXT NOT NULL,
            time_spent TEXT DEFAULT '',
            remark TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS exam_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            test_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            submitted_time TEXT,
            status TEXT DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL,
            FOREIGN KEY (test_id) REFERENCES tests (id) ON DELETE CASCADE
        );
        """
    )
    db.commit()


def migrate_database():
    db = get_db()
    cursor = db.execute("PRAGMA table_info(results)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'user_email' not in columns:
        try:
            db.execute("ALTER TABLE results ADD COLUMN user_email TEXT DEFAULT ''")
            db.commit()
        except:
            pass

    if 'subject' not in columns:
        try:
            db.execute("ALTER TABLE results ADD COLUMN subject TEXT DEFAULT ''")
            db.commit()
        except:
            pass


def table_is_empty(table):
    return db_one(f"SELECT COUNT(*) AS total FROM {table}")["total"] == 0


def seed_database():
    if table_is_empty("subjects"):
        for subject in SUBJECTS:
            db_execute(
                """
                INSERT INTO subjects (id, name, level, materials, tests, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    subject.get("id"),
                    subject.get("name", ""),
                    subject.get("level", ""),
                    subject.get("materials", 0),
                    subject.get("tests", 0),
                    subject.get("description", ""),
                ),
            )

    if table_is_empty("users"):
        for user in USERS:
            db_execute(
                "INSERT INTO users (id, fullname, email, role, registered) VALUES (?, ?, ?, ?, ?)",
                (
                    user.get("id"),
                    user.get("fullname", ""),
                    user.get("email", ""),
                    user.get("role", "Student"),
                    user.get("registered", datetime.now().strftime("%Y-%m-%d %H:%M")),
                ),
            )

    if table_is_empty("materials"):
        for material in MATERIALS:
            db_execute(
                """
                INSERT INTO materials (title, subject, type, file_url, source_url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    material.get("title", ""),
                    material.get("subject", ""),
                    material.get("type", ""),
                    material.get("file_url", ""),
                    material.get("source_url", ""),
                ),
            )

    if table_is_empty("past_papers"):
        for paper in PAST_PAPERS:
            db_execute(
                """
                INSERT INTO past_papers (subject, year, paper, file_url, source_url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    paper.get("subject", ""),
                    paper.get("year", 0),
                    paper.get("paper", ""),
                    paper.get("file_url", ""),
                    paper.get("source_url", ""),
                ),
            )

    if table_is_empty("tests"):
        for test in MOCK_TESTS:
            MOCK_TESTS_DB.append(test)

    if table_is_empty("results"):
        for result in RECENT_RESULTS:
            db_execute(
                """
                INSERT INTO results (test, score, date, time_spent, remark)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    result.get("test", ""),
                    result.get("score", ""),
                    normalize_date(result.get("date")),
                    result.get("time_spent", ""),
                    result.get("remark", ""),
                ),
            )

    if table_is_empty("notifications"):
        for notification in NOTIFICATIONS:
            db_execute("INSERT INTO notifications (message) VALUES (?)", (notification,))


SUBJECTS_DB = DbCollection("subjects", ["name", "level", "materials", "tests", "description"])
USERS_DB = DbCollection("users", ["fullname", "email", "role", "registered"])
MATERIALS_DB = DbCollection("materials", ["title", "subject", "type", "file_url", "source_url"])
PAST_PAPERS_DB = DbCollection("past_papers", ["subject", "year", "paper", "file_url", "source_url"])
MOCK_TESTS_DB = TestCollection()
RECENT_RESULTS_DB = DbCollection("results", ["test", "score", "date", "time_spent", "remark"], "id DESC")
NOTIFICATIONS_DB = DbCollection("notifications", ["message"])
EXAM_ATTEMPTS_DB = ExamAttemptCollection()


with app.app_context():
    create_schema()
    migrate_database()
    seed_database()

SUBJECTS = SUBJECTS_DB
USERS = USERS_DB
MATERIALS = MATERIALS_DB
PAST_PAPERS = PAST_PAPERS_DB
MOCK_TESTS = MOCK_TESTS_DB
RECENT_RESULTS = RECENT_RESULTS_DB
NOTIFICATIONS = NOTIFICATIONS_DB
EXAM_ATTEMPTS = EXAM_ATTEMPTS_DB


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


def form_text(name, default=""):
    return (request.form.get(name) or default).strip()


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
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        # Check for hardcoded admin account
        if email == "admin@gmail.com" and password == "admin123":
            user_role = "admin"
            user_name = "Admin User"
        else:
            # Check if student exists in registered users
            user = next((user for user in USERS if user["email"] == email and user["role"] == "Student"), None)
            if user:
                user_role = "student"
                user_name = user["fullname"]
            else:
                # User not found or not a student
                pending_name = session.get("pending_login_name", "")
                return render_template(
                    "login.html",
                    title="Login",
                    registered=False,
                    error="Invalid email or password",
                    pending_email=email,
                    pending_name=pending_name,
                    next_path=next_path or "",
                )

        session["user_role"] = user_role
        session["user_name"] = user_name
        session["user_email"] = email
        session.pop("pending_login_name", None)
        return redirect_after_auth(user_role)

    registered = request.args.get("registered") == "1"
    return render_template(
        "login.html",
        title="Login",
        registered=registered,
        pending_name=session.get("pending_login_name", ""),
        next_path=session.get("auth_next", ""),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    next_path = request.values.get("next") or session.get("auth_next") or ""
    if is_safe_next_path(next_path):
        session["auth_next"] = next_path

    if request.method == "POST":
        fullname = request.form.get("fullname", "Student User").strip() or "Student User"
        email = request.form.get("email", "").strip()

        # Assign a new unique ID to the user
        next_id = max((u.get("id", 0) for u in USERS), default=0) + 1
        USERS.append({
            "id": next_id,
            "fullname": fullname,
            "email": email,
            "role": "Student",
            "registered": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

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
    # Get current user's email/name from session
    user_email = session.get('user_email')
    user_id = session.get('user_id')

    # Initialize stats with defaults
    stats = {
        'tests_taken': 0,
        'average_score': '0%',
        'materials_read': 0,
        'notifications': 0,
    }

    recent_results = []
    next_test = None

    if user_email:
        # Count tests taken by this student
        tests_taken = db_one(
            "SELECT COUNT(*) as count FROM results WHERE user_email = ?",
            (user_email,)
        )
        stats['tests_taken'] = tests_taken['count'] if tests_taken else 0

        # Calculate average score for this student
        avg_score = db_one(
            "SELECT AVG(CAST(REPLACE(score, '%', '') AS FLOAT)) as avg FROM results WHERE user_email = ?",
            (user_email,)
        )
        if avg_score and avg_score['avg']:
            stats['average_score'] = f"{round(avg_score['avg'])}%"

        # Count materials (or could track materials accessed)
        materials_total = db_one("SELECT COUNT(*) as count FROM materials")
        stats['materials_read'] = materials_total['count'] if materials_total else 0

        # Count unread notifications
        notifications = db_one("SELECT COUNT(*) as count FROM notifications")
        stats['notifications'] = notifications['count'] if notifications else 0

        # Get recent results for this student (limit to 5)
        recent_results = db_all(
            "SELECT test, score, date FROM results WHERE user_email = ? ORDER BY date DESC LIMIT 5",
            (user_email,)
        )
        recent_results = [dict(r) for r in recent_results]

    # Get subject-wise averages for this student
    subject_analytics = []
    if user_email:
        subject_analytics = db_all(
            """SELECT subject, AVG(CAST(REPLACE(score, '%', '') AS FLOAT)) as avg_score
               FROM results WHERE user_email = ? AND subject IS NOT NULL AND subject != ''
               GROUP BY subject LIMIT 4""",
            (user_email,)
        )
        subject_analytics = [dict(r) for r in subject_analytics]

    # Get next available test
    next_test = db_one("SELECT title, duration, marks FROM tests LIMIT 1")
    next_test = dict(next_test) if next_test else None

    return render_template(
        "student/dashboard.html",
        title="Student Dashboard",
        stats=stats,
        recent_results=recent_results,
        subject_analytics=subject_analytics,
        next_test=next_test,
    )


@app.route("/student/profile", methods=["GET", "POST"])
@login_required("student")
def student_profile():
    submitted = False
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        exam_focus = request.form.get("exam_focus", "").strip()
        
        if fullname:
            session["user_name"] = fullname
        if email:
            session["user_email"] = email
        if exam_focus:
            session["exam_focus"] = exam_focus
            
        # Also update the user in USERS list
        current_email = session.get("user_email")
        for u in USERS:
            if u["email"] == current_email or u["fullname"] == session.get("user_name"):
                if fullname:
                    u["fullname"] = fullname
                if email:
                    u["email"] = email
                break
        
        submitted = True
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
    test = MOCK_TESTS.get(test_id) or MOCK_TESTS[0]
    return render_template("student/take_test.html", title="Take Mock Test", test=test, test_id=test_id)


@app.route("/student/mock-tests/<int:test_id>/submit", methods=["POST"])
@login_required("student")
def student_submit_test(test_id):
    test = MOCK_TESTS.get(test_id) or MOCK_TESTS[0]
    elapsed_seconds = form_int("elapsed_seconds")
    attempt_id = request.form.get("attempt_id")
    
    # Mark the attempt as submitted
    if attempt_id:
        EXAM_ATTEMPTS.submit_attempt(int(attempt_id))
    
    questions = test.get("questions", [])
    total_marks = 0
    obtained_marks = 0
    
    if questions:
        for idx, question in enumerate(questions, 1):
            selected_answer = request.form.get(f"q{idx}")
            correct_answer = question.get("answer")
            q_marks = question.get("marks", 1)
            total_marks += q_marks
            if selected_answer == correct_answer:
                obtained_marks += q_marks
        
        percentage = int((obtained_marks / total_marks) * 100) if total_marks > 0 else 100
        score = f"{percentage}%"
    else:
        # Fallback if no questions are defined for this test
        selected_answer = request.form.get("q1")
        if selected_answer == "A":
            score = "100%"
        else:
            score = "0%"
            
    time_left_seconds = (test.get("duration", 60) * 60) - elapsed_seconds

    RECENT_RESULTS.insert(
        0,
        {
            "test": test["title"],
            "score": score,
            "date": datetime.now().isoformat(),
            "time_spent": format_elapsed_time(elapsed_seconds),
            "time_left": format_elapsed_time(max(0, time_left_seconds)),
        },
    )
    
    # Recalculate STUDENT_STATS
    total_percentage = 0
    count = 0
    for res in RECENT_RESULTS:
        score_str = res.get("score", "")
        if "%" in score_str:
            try:
                val = int(score_str.split("%")[0].strip())
                total_percentage += val
                count += 1
            except ValueError:
                pass
    if count > 0:
        STUDENT_STATS["average_score"] = f"{int(total_percentage / count)}%"
    STUDENT_STATS["tests_taken"] = count
    
    return redirect(url_for("student_results"))


@app.route("/api/exam-attempt/start", methods=["POST"])
@login_required("student")
def api_start_exam_attempt():
    """Start a new exam attempt and return the attempt ID"""
    user_id = session.get("user_id", 1)
    test_id = request.json.get("test_id")
    
    if not test_id:
        return jsonify({"error": "test_id is required"}), 400
    
    test = MOCK_TESTS.get(test_id)
    if not test:
        return jsonify({"error": "Test not found"}), 404
    
    # Check if there's already an active attempt
    existing_attempt = EXAM_ATTEMPTS.get_active_attempt(user_id, test_id)
    if existing_attempt:
        attempt_id = existing_attempt["id"]
    else:
        # Create new exam attempt
        attempt_id = EXAM_ATTEMPTS.start_exam(user_id, test_id, test.get("duration", 60))
    
    # Get the attempt status to return current times
    status = EXAM_ATTEMPTS.get_attempt_status(attempt_id)
    return jsonify({
        "attempt_id": attempt_id,
        **status
    }), 200


@app.route("/api/exam-attempt/<int:attempt_id>/status", methods=["GET"])
@login_required("student")
def api_get_exam_attempt_status(attempt_id):
    """Get the current status and remaining time for an exam attempt"""
    status = EXAM_ATTEMPTS.get_attempt_status(attempt_id)
    if not status:
        return jsonify({"error": "Attempt not found"}), 404
    
    return jsonify(status), 200


@app.route("/api/exam-attempt/<int:attempt_id>/submit", methods=["POST"])
@login_required("student")
def api_submit_exam_attempt(attempt_id):
    """Submit an exam attempt"""
    EXAM_ATTEMPTS.submit_attempt(attempt_id)
    return jsonify({"success": True}), 200


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


@app.route("/student/notifications/stream")
@login_required("student")
def notifications_stream():
    def generate():
        # Send current notification count
        yield f"data: {{'count': {len(NOTIFICATIONS)}}}\n\n"

        # Keep connection open and listen for new notifications
        last_count = len(NOTIFICATIONS)
        while True:
            try:
                current_count = len(NOTIFICATIONS)
                if current_count > last_count:
                    new_notif = NOTIFICATIONS[0]
                    yield f"data: {{'message': '{new_notif}', 'count': {current_count}}}\n\n"
                    last_count = current_count

                # Check every second
                import time
                time.sleep(1)
            except GeneratorExit:
                break

    return Response(generate(), mimetype="text/event-stream")


@app.route("/admin/dashboard")
@login_required("admin")
def admin_dashboard():
    # Get total students
    total_students = db_one("SELECT COUNT(*) as count FROM users WHERE role = 'Student'")
    total_students_count = total_students['count'] if total_students else 0

    # Get students added this month
    current_month_start = date.today().replace(day=1).isoformat()
    new_students = db_one(
        "SELECT COUNT(*) as count FROM users WHERE role = 'Student' AND registered >= ?",
        (current_month_start,)
    )
    new_students_count = new_students['count'] if new_students else 0

    # Get average score across all tests
    avg_score = db_one("SELECT AVG(CAST(REPLACE(score, '%', '') AS FLOAT)) as avg FROM results WHERE score != ''")
    avg_score_val = f"{round(avg_score['avg'])}" if avg_score and avg_score['avg'] else "0"

    # Get materials count
    materials_count = db_one("SELECT COUNT(*) as count FROM materials")
    materials_count_val = materials_count['count'] if materials_count else 0

    # Get tests count
    tests_count = db_one("SELECT COUNT(*) as count FROM tests")
    tests_count_val = tests_count['count'] if tests_count else 0

    # Get active tests (just show how many exist, since we don't track creation dates)
    active_tests = tests_count_val

    # Get subject-wise analytics
    subject_analytics = db_all(
        """SELECT subject, AVG(CAST(REPLACE(score, '%', '') AS FLOAT)) as avg_score
           FROM results WHERE subject IS NOT NULL AND subject != '' AND score != ''
           GROUP BY subject ORDER BY avg_score DESC"""
    )

    dashboard_data = {
        'total_students': total_students_count,
        'new_students': new_students_count,
        'avg_score': avg_score_val,
        'materials_count': materials_count_val,
        'tests_count': tests_count_val,
        'active_tests': max(0, active_tests - 2) if active_tests > 2 else active_tests,
        'subject_analytics': subject_analytics,
    }

    return render_template("admin/dashboard.html", title="Admin Dashboard", data=dashboard_data)


@app.route("/admin/users")
@login_required("admin")
def admin_users():
    return render_template("admin/users.html", title="Manage Users", users=USERS)


@app.route("/admin/users/new", methods=["GET", "POST"])
@login_required("admin")
def admin_user_form():
    if request.method == "POST":
        # Assign a new unique ID to the user
        next_id = max((u.get("id", 0) for u in USERS), default=0) + 1
        USERS.append(
            {
                "id": next_id,
                "fullname": request.form.get("fullname", "New User"),
                "email": request.form.get("email", ""),
                "role": request.form.get("role", "Student"),
                "registered": datetime.now().strftime("%Y-%m-%d %H:%M"), # Added for consistency
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
    delete_by_id(USERS, user_id) # Use delete_by_id instead of delete_by_index
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
            {"label": "Material type", "name": "type", "type": "select", "options": ["PDF Notes", "Revision Guide", "Model Answers", "Syllabus"]},
            {"label": "Upload file", "name": "upload_file", "type": "file", "accept": ".pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png"},
            {"label": "External URL", "name": "source_url", "type": "url"},
        ],
    )


@app.route("/admin/materials/<int:material_id>/delete", methods=["POST"])
@login_required("admin")
def admin_delete_material(material_id):
    delete_by_id(MATERIALS, material_id)
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
    delete_by_id(PAST_PAPERS, paper_id)
    return redirect(url_for("admin_past_papers"))


@app.route("/admin/tests")
@login_required("admin")
def admin_tests():
    return render_template("admin/tests.html", title="Manage Tests", tests=MOCK_TESTS, subjects=SUBJECTS)


@app.route("/admin/tests/new", methods=["GET", "POST"])
@app.route("/admin/tests/<int:test_id>/edit", methods=["GET", "POST"])
@login_required("admin")
def admin_test_form(test_id=None):
    test = MOCK_TESTS.get(test_id) if test_id else None

    if request.method == "POST":
        title = form_text("title", "New Test") or "New Test"
        subject = form_text("subject")
        duration = form_int("duration", 60)
        marks = form_int("total_marks", 100)

        if test_id:
            test["title"] = title
            test["subject"] = subject
            test["duration"] = duration
            test["marks"] = marks

            if request.files.get("upload_file"):
                test["file_url"] = save_uploaded_file("upload_file")
                test["file_name"] = request.files.get("upload_file").filename
        else:
            test_data = {
                "title": title,
                "subject": subject,
                "duration": duration,
                "marks": marks,
                "questions": [],
                "file_url": save_uploaded_file("upload_file") if request.files.get("upload_file") else "",
                "file_name": request.files.get("upload_file").filename if request.files.get("upload_file") else "",
            }
            MOCK_TESTS.append(test_data)

        return redirect(url_for("admin_tests"))

    fields = [
        {"label": "Test title", "name": "title", "type": "text", "value": test.get("title") if test else ""},
        {"label": "Subject", "name": "subject", "type": "select", "options": [subject["name"] for subject in SUBJECTS], "value": test.get("subject") if test else ""},
        {"label": "Duration minutes", "name": "duration", "type": "number", "value": test.get("duration", 60) if test else 60},
        {"label": "Total marks", "name": "total_marks", "type": "number", "value": test.get("marks", 100) if test else 100},
        {"label": "Upload test file", "name": "upload_file", "type": "file", "accept": ".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"},
    ]

    return render_template(
        "admin/form.html",
        title="Edit Test" if test else "Create Test",
        submitted=False,
        has_upload=True,
        return_endpoint="admin_tests",
        fields=fields,
    )


@app.route("/admin/tests/<int:test_id>/delete", methods=["POST"])
@login_required("admin")
def admin_delete_test(test_id):
    delete_by_id(MOCK_TESTS, test_id)
    return redirect(url_for("admin_tests"))


@app.route("/admin/tests/upload-external", methods=["GET", "POST"])
@login_required("admin")
def admin_test_upload_external():
    if request.method == "POST":
        uploaded_file_url = save_uploaded_file("upload_file")
        MOCK_TESTS.append(
            {
                "title": form_text("title", "External Test") or "External Test",
                "subject": form_text("subject"),
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


def test_select_options():
    options = []
    for test in MOCK_TESTS:
        title = (test.get("title") or "").strip() or f"Test {test['id']}"
        subject = (test.get("subject") or "").strip()
        label = f"{title} ({subject})" if subject else title
        options.append({"label": label, "value": test["id"]})
    return options


def question_from_form():
    return {
        "text": form_text("question", "New question") or "New question",
        "answer": form_text("correct_answer", "A") or "A",
        "marks": form_int("marks", 1),
        "remark": form_text("remark"),
        "options": [
            form_text("option_a", "Option A"),
            form_text("option_b", "Option B"),
            form_text("option_c", "Option C"),
            form_text("option_d", "Option D"),
        ],
    }


def render_question_form(title, selected_test_id="", question=None):
    question = question or {}
    options = question.get("options") or ["Option A", "Option B", "Option C", "Option D"]
    return render_template(
        "admin/form.html",
        title=title,
        submitted=False,
        return_endpoint="admin_questions",
        fields=[
            {"label": "Test", "name": "test_id", "type": "select", "options": test_select_options(), "value": selected_test_id},
            {"label": "Question", "name": "question", "type": "textarea", "value": question.get("text", "")},
            {"label": "Option A", "name": "option_a", "type": "text", "value": options[0]},
            {"label": "Option B", "name": "option_b", "type": "text", "value": options[1]},
            {"label": "Option C", "name": "option_c", "type": "text", "value": options[2]},
            {"label": "Option D", "name": "option_d", "type": "text", "value": options[3]},
            {"label": "Correct answer", "name": "correct_answer", "type": "select", "options": ["A", "B", "C", "D"], "value": question.get("answer", "A")},
            {"label": "Marks", "name": "marks", "type": "number", "value": question.get("marks", 1)},
            {"label": "Remarks", "name": "remark", "type": "textarea", "value": question.get("remark", "")},
        ],
    )


@app.route("/admin/questions/new", methods=["GET", "POST"])
@login_required("admin")
def admin_question_form():
    if request.method == "POST":
        selected_test_id = form_int("test_id", 0)
        test = MOCK_TESTS.get(selected_test_id)
        if test:
            test.setdefault("questions", []).append(question_from_form())
        return redirect(url_for("admin_questions"))

    selected_test_id = request.args.get("test_id", type=int) or (MOCK_TESTS[0]["id"] if MOCK_TESTS else "")
    return render_question_form("Add Question", selected_test_id)


@app.route("/admin/questions/<int:test_id>/<int:question_id>/edit", methods=["GET", "POST"])
@login_required("admin")
def admin_edit_question(test_id, question_id):
    test = MOCK_TESTS.get(test_id)
    if not test:
        return redirect(url_for("admin_questions"))

    questions = test.setdefault("questions", [])
    question = questions.get(question_id)
    if not question:
        return redirect(url_for("admin_questions"))

    if request.method == "POST":
        selected_test_id = form_int("test_id", test_id)
        updated_question = question_from_form()
        selected_test = MOCK_TESTS.get(selected_test_id)
        if selected_test:
            if selected_test_id == test_id:
                questions.replace(question_id, updated_question)
            else:
                questions.delete(question_id)
                selected_test.setdefault("questions", []).append(updated_question)
        return redirect(url_for("admin_questions"))

    return render_question_form("Edit Question", test_id, question)


@app.route("/admin/questions/<int:test_id>/<int:question_id>/delete", methods=["POST"])
@login_required("admin")
def admin_delete_question(test_id, question_id):
    test = MOCK_TESTS.get(test_id)
    if test:
        questions = test.setdefault("questions", [])
        if questions.get(question_id):
            questions.delete(question_id)
    return redirect(url_for("admin_questions"))


@app.route("/admin/reports")
@login_required("admin")
def admin_reports():
    return render_template("admin/reports.html", title="Reports", results=RECENT_RESULTS)


@app.route("/admin/reports/<int:result_id>/remark", methods=["POST"])
@login_required("admin")
def admin_update_report_remark(result_id):
    result = RECENT_RESULTS.get(result_id)
    if result:
        RECENT_RESULTS.update_field(result_id, "remark", form_text("remark"))
    return redirect(url_for("admin_reports"))


@app.route("/admin/reports/<int:result_id>/remark/delete", methods=["POST"])
@login_required("admin")
def admin_delete_report_remark(result_id):
    result = RECENT_RESULTS.get(result_id)
    if result:
        RECENT_RESULTS.update_field(result_id, "remark", "")
    return redirect(url_for("admin_reports"))


@app.route("/admin/reports/<int:result_id>/delete", methods=["POST"])
@login_required("admin")
def admin_delete_result(result_id):
    delete_by_id(RECENT_RESULTS, result_id)
    return redirect(url_for("admin_reports"))


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
