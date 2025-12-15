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
    Flask, render_template, request, redirect, url_for, flash, session,
    send_file, abort, get_flashed_messages, jsonify
)
from werkzeug.utils import secure_filename

# ✅ WeasyPrint (Render-compatible)
from weasyprint import HTML as WeasyHTML

import firebase_admin
from firebase_admin import credentials, firestore

import config
import dotenv

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
app.secret_key = app.config.get('SECRET_KEY', os.environ.get('FLASK_SECRET', 'dev-secret'))
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# --------------------------------------------------
# FOLDERS
# --------------------------------------------------
UPLOAD_FOLDER = app.config.get('UPLOAD_FOLDER', 'uploads')
GENERATED_FOLDER = app.config.get('GENERATED_FOLDER', 'generated_letters')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'permission_letters'), exist_ok=True)

# --------------------------------------------------
# FIREBASE INIT
# --------------------------------------------------
firebase_cred = os.environ.get("FIREBASE_CREDENTIALS")
if not firebase_cred:
    raise RuntimeError("FIREBASE_CREDENTIALS env var not set")

try:
    cred = credentials.Certificate(json.loads(firebase_cred))
except json.JSONDecodeError:
    if not os.path.isfile(firebase_cred):
        raise RuntimeError("Invalid FIREBASE_CREDENTIALS value")
    cred = credentials.Certificate(firebase_cred)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --------------------------------------------------
# CONSTANTS / HELPERS
# --------------------------------------------------
ALLOWED_EXT = {"pdf"}
COLLECTION = "internship_requests"

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def to_obj(d: dict):
    return SimpleNamespace(**d)

def admin_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return inner

def image_to_data_uri(path: Path) -> str | None:
    if not path.is_file():
        return None
    data = path.read_bytes()
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(data).decode()

# --------------------------------------------------
# PUBLIC ROUTES
# --------------------------------------------------
@app.route('/', methods=['GET'])
def index():
    all_msgs = get_flashed_messages(with_categories=True)
    for cat, msg in all_msgs:
        if cat != 'login':
            flash(msg, cat)
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        name = request.form.get('full_name', '').strip()
        college = request.form.get('college_name', '').strip()
        email = request.form.get('email', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        duration = request.form.get('duration', '').strip()
        student_year = request.form.get('student_year', '').strip()
        branch = request.form.get('branch', '').strip()
        other_branch = request.form.get('other_branch', '').strip()
        submission_date = request.form.get('submission_date') or datetime.utcnow().strftime('%Y-%m-%d')

        if not (name and college and email and start_date and end_date and duration):
            flash('All fields are required.', 'danger')
            return redirect(url_for('index'))

        file = request.files.get('permission_letter')
        if not file or not allowed_file(file.filename):
            flash('Valid PDF permission letter required.', 'danger')
            return redirect(url_for('index'))

        fname = secure_filename(file.filename)
        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        saved = f"{ts}_{fname}"
        save_path = Path(UPLOAD_FOLDER) / "permission_letters" / saved
        file.save(save_path)

        doc_ref = db.collection(COLLECTION).document()
        doc_ref.set({
            "doc_id": doc_ref.id,
            "student_name": name,
            "college_name": college,
            "email": email,
            "start_date": start_date,
            "end_date": end_date,
            "duration": duration,
            "student_year": student_year,
            "branch": branch or other_branch,
            "permission_path": f"permission_letters/{saved}",
            "status": "pending",
            "submission_date": submission_date,
            "created_at": datetime.utcnow().isoformat()
        })

        flash('Application submitted successfully.', 'success')
        return redirect(url_for('index'))

    except Exception as e:
        logger.exception("Submit error")
        flash(str(e), 'danger')
        return redirect(url_for('index'))

# --------------------------------------------------
# ADMIN AUTH
# --------------------------------------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if (request.form.get('username') == app.config.get('ADMIN_USERNAME') and
            request.form.get('password') == app.config.get('ADMIN_PASSWORD')):
            session['admin_logged_in'] = True
            flash('Logged in successfully.', 'login')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('admin_login'))

# --------------------------------------------------
# ADMIN DASHBOARD & VIEW
# --------------------------------------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    docs = db.collection(COLLECTION).order_by(
        'created_at', direction=firestore.Query.DESCENDING
    ).stream()
    rows = [to_obj(d.to_dict() | {"doc_ref_id": d.id}) for d in docs]
    return render_template('admin.html', requests=rows)

@app.route('/admin/view/<req_id>')
@admin_required
def admin_view(req_id):
    doc = db.collection(COLLECTION).document(req_id).get()
    if not doc.exists:
        abort(404)

    data = doc.to_dict()

    # ✅ Normalize status (CRITICAL FIX)
    status = (data.get("status") or "pending").lower()

    # ✅ Map fields expected by view_request.html
    context = {
        "req_id": req_id,
        "student_name": data.get("student_name"),
        "email": data.get("email"),
        "college": data.get("college_name"),
        "year": data.get("student_year"),
        "branch": data.get("branch"),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "duration": data.get("duration"),
        "submission": data.get("submission_date"),
        "status": status,

        # permission file
        "permission_filename": (
            data.get("permission_path").split("/", 1)[1]
            if data.get("permission_path") else None
        ),

        # generated letter
        "generated_filename": data.get("generated_letter_filename"),
    }

    return render_template("view_request.html", **context)

# --------------------------------------------------
# APPROVE (WeasyPrint)
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
        letter_year=datetime.utcnow().year,
        issued_date=issued,
        header_image=header_img
    )

    pdf_name = f"offer_{req_id}.pdf"
    pdf_path = Path(GENERATED_FOLDER) / pdf_name

    WeasyHTML(string=html, base_url=request.host_url).write_pdf(pdf_path)

    doc_ref.update({
        "status": "approved",
        "generated_letter_filename": pdf_name,
        "issued_date": issued
    })

    flash("Request approved and letter generated.", "success")
    return redirect(url_for('admin_view', req_id=req_id))

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
    return redirect(url_for('admin_view', req_id=req_id))

# --------------------------------------------------
# FILE SERVING
# --------------------------------------------------
@app.route('/uploads/<path:filename>')
@admin_required
def uploaded_file(filename):
    path = Path(UPLOAD_FOLDER) / filename
    if not path.is_file():
        abort(404)
    return send_file(path)

@app.route('/generated_letters/<filename>')
@admin_required
def serve_generated(filename):
    path = Path(GENERATED_FOLDER) / secure_filename(filename)
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
# MAIN
# --------------------------------------------------
if __name__ == '__main__':
    logger.info("Starting Flask + Firestore JNPA app")
    app.run(debug=True)
