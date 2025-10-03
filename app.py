import os
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import sqlite3
from datetime import datetime
from io import StringIO, BytesIO
import csv

# Config from environment (defaults set for zero-config deploy)
APP_SECRET = os.getenv("APP_SECRET", "please-change-this-secret")
ADMIN_USER = os.getenv("ADMIN_USER", "R&bmedical")
ADMIN_PASS = os.getenv("ADMIN_PASS", "Er090909")
DB_PATH = os.getenv("DB_PATH", "attendance.db")

app = Flask(__name__)
app.secret_key = APP_SECRET

# --- Database helpers ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee TEXT NOT NULL,
            action TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_record(employee, action):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO attendance (employee, action, time) VALUES (?, ?, ?)", (employee, action, now))
    conn.commit()
    conn.close()
    return now

def get_records(limit=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    q = "SELECT id, employee, action, time FROM attendance ORDER BY id DESC"
    if limit:
        q += f" LIMIT {int(limit)}"
    c.execute(q)
    rows = c.fetchall()
    conn.close()
    return rows

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    if request.method == "POST":
        employee = request.form.get("employee", "").strip()
        action = request.form.get("action")
        if not employee:
            message = "Please enter your name or ID."
        else:
            time_str = add_record(employee, action)
            message = f"{employee} {action} at {time_str}"
    return render_template("index.html", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "")
        pwd = request.form.get("password", "")
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))
    records = get_records()
    return render_template("dashboard.html", records=records)

@app.route("/export")
def export_csv():
    if not session.get("admin"):
        return redirect(url_for("login"))
    rows = get_records(limit=None)
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID","Employee","Action","Time"])
    for r in rows[::-1]:
        writer.writerow(r)
    output = si.getvalue().encode("utf-8")
    return send_file(BytesIO(output), as_attachment=True, download_name="attendance_export.csv", mimetype="text/csv")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# Initialize DB on startup
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
