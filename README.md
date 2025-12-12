```md
# 🚢 JNPA Internship Letter Generator

A Flask-based web app to generate **official Internship Permission Letters** for the **Jawaharlal Nehru Port Authority (JNPA)**.  
Generates bilingual (Hindi + English) letters with correct Devanagari fonts, clean A4 layout, header/footer, and PDF export.

> Copy-paste this file as `README.md` at the root of your repo.

---

## ✨ Features

- 📄 Generate official JNPA Internship Letters (bilingual)
- 🇮🇳 Devanagari (Hindi) font support
- 🧾 Auto-filled student info, internship period, and college details
- 📐 A4-friendly layout with margins, header, footer
- 🖨️ PDF export using `wkhtmltopdf` (or compatible engine)
- 🛠️ Simple admin UI to review requests and produce letters
- 🗂️ Static assets support for logos, fonts, and decorative patterns

---

## 📁 Project structure

```

jnpa-internship-letter-generator/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── static/
│   ├── fonts/           # Devanagari and other fonts
│   └── img/             # logos, patterns
│
├── templates/
│   ├── admin.html
│   ├── form.html
│   ├── internship_letter.html
│   ├── login.html
│   └── view_request.html
│
├── uploads/             # user uploads (ignored in git)
└── generated_letters/   # generated PDFs (ignored in git)

````

---

## ⚙️ Quick install & run (copy-paste)

### 1. Clone repository
```bash
git clone https://github.com/<your-username>/jnpa-internship-letter-generator.git
cd jnpa-internship-letter-generator
````

### 2. Create & activate virtualenv

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install requirements

```bash
pip install -r requirements.txt
```

### 4. Install `wkhtmltopdf` (required for PDF)

Download from: [https://wkhtmltopdf.org/downloads.html](https://wkhtmltopdf.org/downloads.html)
Make sure the `wkhtmltopdf` binary is accessible via your system `PATH`.

### 5. Start the app

**Optional (set env var):**

```bash
# Windows
set FLASK_APP=app.py

# macOS / Linux
export FLASK_APP=app.py
```

**Run**

```bash
flask run
```

Open your browser: `http://127.0.0.1:5000`

---

## 🔧 Configuration tips

* Put Devanagari/Unicode fonts (e.g., `NotoSansDevanagari-Regular.ttf`) in:

  ```
  static/fonts/
  ```

  Reference them in your `internship_letter.html` with `@font-face` so wkhtmltopdf picks them up.

* Put logos in:

  ```
  static/img/
  ```

* Ensure `generated_letters/` and `uploads/` are writeable by the Flask process.

---

## ✅ Example `.gitignore` (copy-paste into `.gitignore`)

```
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
*.sqlite3
generated_letters/
uploads/
.env
*.log
*.pdf
```

---

## 🧩 Minimal `requirements.txt` example

```
Flask>=2.0
Flask-WTF
pdfkit
wkhtmltopdf  # optional note: actual wkhtmltopdf is a system binary, not a pip package
```

> Recommended real-world libs you may already use: `Flask`, `pdfkit` (Python wrapper), `Jinja2` (Flask uses it), `Werkzeug`. Adjust versions as needed.

---

## 💡 Helpful tips & gotchas

* `wkhtmltopdf` must be the correct architecture for your OS. If PDFs look wrong (fonts missing), point `pdfkit` / wkhtmltopdf to fonts via absolute file paths and use `@font-face` in the HTML/CSS.
* If you see strange characters in Hindi, confirm the letter HTML uses `<meta charset="utf-8">`, fonts are declared, and the PDF engine can access them.
* When testing locally, open the HTML `internship_letter.html` in browser to verify layout before PDF generation.

---

## 🧾 License

This repository is intended for **educational and internal use only**.

---



```
```
