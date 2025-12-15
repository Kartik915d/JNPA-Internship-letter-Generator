# app.py
import os
import json
import logging
import base64
from datetime import datetime
from types import SimpleNamespace
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, send_file, abort, get_flashed_messages
)

from weasyprint import HTML  # ✅ WeasyPrint ONLY

import firebase_admin
from firebase_admin import credentials, firestore

import dotenv
import config

# --------------------------------------------------
# ENV + LOGGING
# --------------------------------------------------
dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# FLASK APP
# --------------------------------------------------
app = Flask(__name__)
app.config.from_object(config)
app.secret_key = app.config.get(
    "SECRET_KEY",
    os.environ.get("FLASK_SECRET", "dev-secret")
)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True

# --------------------------------------------------
# FOLDERS
# --------------------------------------------------
UPLOAD_FOLDER = app.config.get("UPLOAD_FOLDER", "uploads")
GENERATED_FOLDER = app.config.get("GENERATED_FOLDER", "generated_letters")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "permission_letters"), exist_ok=True)

# --------------------------------------------------
# FIREBASE INIT (RAILWAY + LOCAL SAFE)
# --------------------------------------------------
firebase_cred = os.environ.get("FIREBASE_CREDENTIALS")
if not firebase_cred:
    raise RuntimeError("FIREBASE_CREDENTIALS env var not set")

try:
    # Railway: JSON string
    cred_dict = json.loads(firebase_cred)
    cred = credentials.Certificate(cred_dict)
except json.JSONDecodeError:
    # Local: file path
    if not os.path.isfile(firebase_cred):
        raise RuntimeError("Invalid FIREBASE_CREDENTIALS value")
    cred = credentials.Certificate(firebase_cred)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------
COLLECTION = "internship_requests"
ALLOWED_EXT = {"pdf"}

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrap

def to_obj(d):
    return SimpleNamespace(**d)

def image_to_data_uri(path: Path):
    if not path.is_file():
        return None
    data = path.read_bytes()
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(data).decode()

# --------------------------------------------------
# PUBLIC ROUTE
# --------------------------------------------------
@app.route("/")
def index():
    msgs = get_flashed_messages(with_categories=True)
    for c, m in msgs:
        if c != "login":
            flash(m, c)
    return render_template("form.html")

# --------------------------------------------------
# ADMIN AUTH
# --------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (
            request.form.get("username") == app.config.get("ADMIN_USERNAME")
            and request.form.get("password") == app.config.get("ADMIN_PASSWORD")
        ):
            session["admin_logged_in"] = True
            flash("Logged in successfully.", "login")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("admin_login"))

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
@app.route("/admin")
@admin_required
def admin_dashboard():
    docs = db.collection(COLLECTION).order_by(
        "created_at", direction=firestore.Query.DESCENDING
    ).stream()

    rows = []
    for d in docs:
        data = d.to_dict() or {}
        data["doc_ref_id"] = d.id
        data["status"] = (data.get("status") or "pending").lower()
        rows.append(to_obj(data))

    return render_template("admin.html", requests=rows)

# --------------------------------------------------
# VIEW REQUEST (FIXED)
# --------------------------------------------------
@app.route("/admin/view/<req_id>")
@admin_required
def admin_view(req_id):
    doc = db.collection(COLLECTION).document(req_id).get()
    if not doc.exists:
        abort(404)

    data = doc.to_dict() or {}
    status = (data.get("status") or "pending").lower()

    permission = data.get("permission_path")
    if permission:
        permission = permission.replace("\\", "/")

    return render_template(
        "view_request.html",
        req_id=req_id,
        student_name=data.get("student_name"),
        email=data.get("email"),
        college=data.get("college_name"),
        year=data.get("student_year"),
        branch=data.get("branch"),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        duration=data.get("duration"),
        submission=data.get("submission_date"),
        status=status,
        permission_filename=permission,
        generated_filename=data.get("generated_letter_filename"),
    )

# --------------------------------------------------
# PREVIEW GENERATED LETTER
# --------------------------------------------------
@app.route("/admin/preview/<req_id>")
@admin_required
def preview_letter(req_id):
    doc = db.collection(COLLECTION).document(req_id).get()
    if not doc.exists:
        abort(404)

    data = doc.to_dict()
    if (data.get("status") or "").lower() != "approved":
        abort(403)

    fname = data.get("generated_letter_filename")
    if not fname:
        abort(404)

    pdf_path = Path(GENERATED_FOLDER) / fname
    if not pdf_path.is_file():
        abort(404)

    return send_file(pdf_path, mimetype="application/pdf")

# --------------------------------------------------
# APPROVE (WEASYPRINT ONLY)
# --------------------------------------------------
@app.route("/admin/approve/<req_id>", methods=["POST"])
@admin_required
def admin_approve(req_id):
    doc_ref = db.collection(COLLECTION).document(req_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404)

    data = doc.to_dict() or {}
    issued = datetime.utcnow().strftime("%d-%m-%Y")

    header_img = image_to_data_uri(
        Path(app.static_folder) / "img/Fjnpa_logo.png"
    )

    html = render_template(
        "internship_letter.html",
        **data,
        issued_date=issued,
        header_image=header_img,
        letter_year=datetime.utcnow().year,
    )

    pdf_name = f"offer_{req_id}.pdf"
    pdf_path = Path(GENERATED_FOLDER) / pdf_name

    # ✅ WeasyPrint ONLY
    HTML(string=html, base_url=request.host_url).write_pdf(str(pdf_path))

    doc_ref.update({
        "status": "approved",
        "generated_letter_filename": pdf_name,
        "issued_date": issued,
    })

    flash("Request approved and letter generated.", "success")
    return redirect(url_for("admin_view", req_id=req_id))

# --------------------------------------------------
# REJECT
# --------------------------------------------------
@app.route("/admin/reject/<req_id>", methods=["POST"])
@admin_required
def admin_reject(req_id):
    db.collection(COLLECTION).document(req_id).update({
        "status": "rejected",
        "generated_letter_filename": None
    })
    flash("Request rejected.", "info")
    return redirect(url_for("admin_view", req_id=req_id))

# --------------------------------------------------
# FILE SERVING
# --------------------------------------------------
@app.route("/uploads/<path:filename>")
@admin_required
def uploaded_file(filename):
    path = Path(UPLOAD_FOLDER) / filename
    if not path.is_file():
        abort(404)
    return send_file(path)

@app.route("/download_letter/<req_id>")
@admin_required
def download_letter(req_id):
    pdf_path = Path(GENERATED_FOLDER) / f"offer_{req_id}.pdf"
    if not pdf_path.is_file():
        abort(404)
    return send_file(pdf_path, as_attachment=True)

# --------------------------------------------------
# HEALTH CHECK (IMPORTANT FOR RAILWAY)
# --------------------------------------------------
@app.route("/health")
def health():
    return "OK", 200

# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
