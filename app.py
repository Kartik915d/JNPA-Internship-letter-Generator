# app.py
import os
import logging
import base64
from datetime import datetime
from types import SimpleNamespace
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session,
    send_file, abort, get_flashed_messages, jsonify
)
from werkzeug.utils import secure_filename

import pdfkit
try:
    from weasyprint import HTML as WeasyHTML
    WEASY_AVAILABLE = True
except Exception:
    WEASY_AVAILABLE = False

import firebase_admin
from firebase_admin import credentials, firestore

import config
import dotenv

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# APP
# --------------------------------------------------
app = Flask(__name__)
app.config.from_object(config)
app.secret_key = app.config.get('SECRET_KEY', os.environ.get('FLASK_SECRET', 'dev-secret'))
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

UPLOAD_FOLDER = app.config.get('UPLOAD_FOLDER', 'uploads')
GENERATED_FOLDER = app.config.get('GENERATED_FOLDER', 'generated_letters')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'permission_letters'), exist_ok=True)

# --------------------------------------------------
# FIREBASE
# --------------------------------------------------
cred_path = os.getenv("FIREBASE_CREDENTIALS")
if not cred_path or not os.path.isfile(cred_path):
    raise RuntimeError("FIREBASE_CREDENTIALS not set correctly")

cred = credentials.Certificate(cred_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

COLLECTION = "internship_requests"
ALLOWED_EXT = {"pdf"}

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def allowed_file(fn):
    return "." in fn and fn.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def to_obj(d):
    return SimpleNamespace(**d)

def admin_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*a, **kw)
    return wrap

def image_to_data_uri(path):
    p = Path(path)
    if not p.is_file():
        return None
    data = p.read_bytes()
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(data).decode()

# --------------------------------------------------
# PUBLIC
# --------------------------------------------------
@app.route('/')
def index():
    msgs = get_flashed_messages(with_categories=True)
    for c, m in msgs:
        if c != "login":
            flash(m, c)
    return render_template("form.html")

# --------------------------------------------------
# ADMIN AUTH
# --------------------------------------------------
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == "POST":
        if (request.form.get("username") == app.config.get("ADMIN_USERNAME") and
            request.form.get("password") == app.config.get("ADMIN_PASSWORD")):
            session["admin_logged_in"] = True
            flash("Logged in successfully", "login")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("admin_login"))

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    docs = db.collection(COLLECTION).order_by(
        "created_at", direction=firestore.Query.DESCENDING
    ).stream()
    rows = []
    for d in docs:
        x = d.to_dict()
        x["doc_ref_id"] = d.id
        x["status"] = (x.get("status") or "pending").lower()
        rows.append(to_obj(x))
    return render_template("admin.html", requests=rows)

# --------------------------------------------------
# VIEW REQUEST (🔥 FIXED)
# --------------------------------------------------
@app.route('/admin/view/<req_id>')
@admin_required
def admin_view(req_id):
    doc = db.collection(COLLECTION).document(req_id).get()
    if not doc.exists:
        abort(404)

    data = doc.to_dict()

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
        generated_filename=data.get("generated_letter_filename")
    )

# --------------------------------------------------
# PREVIEW GENERATED LETTER (🔥 NEW)
# --------------------------------------------------
@app.route('/admin/preview/<req_id>')
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

    path = Path(GENERATED_FOLDER) / fname
    if not path.is_file():
        abort(404)

    return send_file(path, mimetype="application/pdf")

# --------------------------------------------------
# APPROVE
# --------------------------------------------------
@app.route('/admin/approve/<req_id>', methods=['POST'])
@admin_required
def admin_approve(req_id):
    doc_ref = db.collection(COLLECTION).document(req_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404)

    data = doc.to_dict()
    issued = datetime.utcnow().strftime('%d-%m-%Y')

    header_img = image_to_data_uri(
        Path(app.static_folder) / "img/Fjnpa_logo.png"
    )

    html = render_template(
        "internship_letter.html",
        **data,
        issued_date=issued,
        header_image=header_img,
        letter_year=datetime.utcnow().year
    )

    pdf_name = f"offer_{req_id}.pdf"
    pdf_path = Path(GENERATED_FOLDER) / pdf_name

    if WEASY_AVAILABLE:
        WeasyHTML(string=html, base_url=request.host_url).write_pdf(pdf_path)
    else:
        pdfkit.from_string(html, str(pdf_path))

    doc_ref.update({
        "status": "approved",
        "generated_letter_filename": pdf_name,
        "issued_date": issued
    })

    flash("Request approved and letter generated.", "success")
    return redirect(url_for("admin_view", req_id=req_id))

# --------------------------------------------------
# REJECT
# --------------------------------------------------
@app.route('/admin/reject/<req_id>', methods=['POST'])
@admin_required
def admin_reject(req_id):
    db.collection(COLLECTION).document(req_id).update({
        "status": "rejected",
        "generated_letter_filename": None
    })
    flash("Request rejected.", "info")
    return redirect(url_for("admin_view", req_id=req_id))

# --------------------------------------------------
# FILE SERVE
# --------------------------------------------------
@app.route('/uploads/<path:filename>')
@admin_required
def uploaded_file(filename):
    path = Path(UPLOAD_FOLDER) / filename
    if not path.is_file():
        abort(404)
    return send_file(path)

@app.route('/download_letter/<req_id>')
@admin_required
def download_letter(req_id):
    path = Path(GENERATED_FOLDER) / f"offer_{req_id}.pdf"
    if not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True)

# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
