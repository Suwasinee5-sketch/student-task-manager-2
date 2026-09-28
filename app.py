"""Attendance Predictor - Flask routes only. Calculations live in services/."""
import os
from datetime import date
from flask import Flask, render_template, request, jsonify, abort
from pathlib import Path
from services import dataset_service as dsv, sample_data as ds, prediction_service as pred

app = Flask(__name__)
# Configurable settings (override via environment variables).
app.config.update(
    SEMESTER_START=date.fromisoformat(os.getenv("SEMESTER_START", "2026-08-29")),
    SEMESTER_END=date.fromisoformat(os.getenv("SEMESTER_END", "2026-11-29")),
    TARGET_PCT=float(os.getenv("TARGET_PCT", 90)),
    DETENTION_PCT=float(os.getenv("DETENTION_PCT", 75)),
    UPCOMING_LIMIT=int(os.getenv("UPCOMING_LIMIT", 10)),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5 MB upload cap
    UPLOAD_DIR=str(Path(__file__).parent / "data" / "uploads"),
    SAMPLE_DATASET=str(Path(__file__).parent / "data" / "sample_timetable.csv"),
)
# Module 2: load the sample timetable as the initial active dataset (replace with the real file later).
dsv.ingest_file(app.config["SAMPLE_DATASET"], app.config["SEMESTER_START"], app.config["SEMESTER_END"])


def _report(section_id, student_id, rate=None):
    """Fetch data and delegate all maths to prediction_service."""
    student = ds.get_student(section_id, student_id)
    if not student:
        return None
    cfg = app.config
    start = max(date.today(), cfg["SEMESTER_START"])  # classes from today onwards
    upcoming = ds.get_upcoming_classes(section_id, start, cfg["SEMESTER_END"])
    return pred.build_report(student, upcoming, len(upcoming), cfg, rate)


@app.route("/")
def index():
    return render_template("index.html", cfg=app.config)


@app.route("/dashboard")
def dashboard():
    sections = ds.list_sections()
    section_id = request.args.get("section") or sections[0]["id"]
    students = ds.get_students(section_id)
    ids = [s["id"] for s in students]
    student_id = request.args.get("student")
    if student_id not in ids:
        student_id = ids[0] if ids else None
    return render_template("dashboard.html", cfg=app.config, sections=sections,
                           students=students, section_id=section_id,
                           student_id=student_id, r=_report(section_id, student_id))


@app.route("/api/report")
def api_report():
    rate = request.args.get("rate", type=float)
    r = _report(request.args.get("section"), request.args.get("student"), rate)
    return (jsonify(r) if r else (jsonify(error="Unknown section/student"), 404))


def _upload_page(report=None, error=None, status=200):
    return render_template("admin_upload.html", report=report, error=error,
                           active=dsv.get_active_info(), cfg=app.config), status


@app.route("/admin/upload", methods=["GET", "POST"])
def admin_upload():
    """Local-testing only: loopback clients can upload and validate a dataset."""
    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403)
    if request.method == "GET":
        return _upload_page()
    try:
        path = dsv.save_upload(request.files.get("dataset"), app.config["UPLOAD_DIR"])
    except dsv.DatasetError as e:
        return _upload_page(error=str(e), status=400)
    return _upload_page(report=dsv.ingest_file(path, app.config["SEMESTER_START"], app.config["SEMESTER_END"]))


@app.errorhandler(413)
def too_large(_):
    return _upload_page(error="File too large (limit 5 MB).", status=413)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=os.getenv("FLASK_DEBUG") == "1")
