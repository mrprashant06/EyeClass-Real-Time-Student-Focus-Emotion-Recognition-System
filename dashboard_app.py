from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
import pandas as pd
import os
from datetime import datetime

STUDENTS_CSV = "students.csv"
CLASS_REPORT_CSV = "class_report.csv"

app = Flask(__name__)


# ---------- Helper functions ----------

def load_students():
    if not os.path.exists(STUDENTS_CSV):
        return pd.DataFrame(columns=["roll_no", "name", "department", "section", "image_path", "email", "phone"])

    df = pd.read_csv(STUDENTS_CSV)
    # Clean column names and strip extra spaces
    df.columns = [c.strip() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    # NEW: also store just the image filename (e.g. "1.jpg", "22.png")
    if "image_path" in df.columns:
        df["image_file"] = df["image_path"].apply(lambda p: os.path.basename(str(p)))
    else:
        df["image_file"] = ""

    return df


def load_reports():
    if not os.path.exists(CLASS_REPORT_CSV):
        return pd.DataFrame(columns=[
            "Roll No", "Name", "Department", "Section",
            "Session Date", "Session Time", "Status",
            "% Time Present (approx)", "% Time Attentive", "Dominant Emotion"
        ])

    df = pd.read_csv(CLASS_REPORT_CSV)
    df.columns = [c.strip() for c in df.columns]
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()
    return df


# ---------- Routes ----------

@app.route("/")
def home():
    """
    Main dashboard: summary + today's stats.
    """
    students_df = load_students()
    reports_df = load_reports()

    total_students = len(students_df)

    # Today’s date
    today = datetime.now().date().isoformat()

    today_reports = reports_df[reports_df["Session Date"] == today] if not reports_df.empty else pd.DataFrame()

    if not today_reports.empty:
        present_count = (today_reports["Status"] == "Present").sum()
        absent_count = (today_reports["Status"] == "Absent").sum()
    else:
        present_count = 0
        absent_count = total_students  # if no report, assume all absent (for display)

    # Recent sessions (list of unique dates + time)
    recent_sessions = []
    if not reports_df.empty:
        recent_sessions = (
            reports_df[["Session Date", "Session Time"]]
            .drop_duplicates()
            .sort_values(["Session Date", "Session Time"], ascending=False)
            .head(10)
            .to_dict(orient="records")
        )

    return render_template(
        "dashboard.html",
        total_students=total_students,
        present_count=present_count,
        absent_count=absent_count,
        today=today,
        recent_sessions=recent_sessions
    )


@app.route("/students")
def students():
    """
    Show all registered students with filters.
    """
    students_df = load_students()

    department = request.args.get("department", "").strip()
    section = request.args.get("section", "").strip()

    filtered_df = students_df.copy()

    if department:
        filtered_df = filtered_df[filtered_df["department"].str.lower() == department.lower()]
    if section:
        filtered_df = filtered_df[filtered_df["section"].str.lower() == section.lower()]

    # For dropdowns
    departments = sorted(students_df["department"].dropna().unique().tolist()) if not students_df.empty else []
    sections = sorted(students_df["section"].dropna().unique().tolist()) if not students_df.empty else []

    return render_template(
        "students.html",
        students=filtered_df.to_dict(orient="records"),
        departments=departments,
        sections=sections,
        selected_department=department,
        selected_section=section
    )


@app.route("/sessions")
def sessions():
    """
    Show list of all sessions (date+time).
    """
    reports_df = load_reports()

    if reports_df.empty:
        sessions_list = []
    else:
        sessions_list = (
            reports_df[["Session Date", "Session Time"]]
            .drop_duplicates()
            .sort_values(["Session Date", "Session Time"], ascending=False)
            .to_dict(orient="records")
        )

    return render_template("sessions.html", sessions=sessions_list)


@app.route("/sessions/view")
def view_session():
    """
    View detailed attendance for a specific session (date + time).
    """
    date = request.args.get("date")
    time_ = request.args.get("time")

    reports_df = load_reports()

    if reports_df.empty or not date or not time_:
        session_rows = []
    else:
        session_rows = reports_df[
            (reports_df["Session Date"] == date) &
            (reports_df["Session Time"] == time_)
        ].to_dict(orient="records")

    return render_template(
        "session_detail.html",
        session_date=date,
        session_time=time_,
        rows=session_rows
    )


@app.route("/reports/download")
def download_reports():
    """
    Download full class_report.csv
    """
    if not os.path.exists(CLASS_REPORT_CSV):
        return "No report found yet.", 404

    return send_file(CLASS_REPORT_CSV, as_attachment=True)


@app.route("/student_image/<filename>")
def student_image(filename):
    """
    Serve student profile images from the 'students' folder.
    """
    return send_from_directory("students", filename)


if __name__ == "__main__":
    app.run(debug=True)
