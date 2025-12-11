
# ✅ **FINAL README.md (Copy–Paste as is)**

```md
# JNPA Internship Letter Generator

This project is a Flask-based web application designed to generate official Internship Permission Letters for the Jawaharlal Nehru Port Authority (JNPA). The system produces bilingual (Hindi + English) letters using the official JNPA format, complete with header, footer, margins, and PDF export support.

The generator ensures consistent formatting, correct Devanagari font rendering, and an automated workflow for creating internship letters.

---

## Features

- Generate official JNPA Internship Letters
- Hindi + English letterhead support with Devanagari fonts
- Auto-filled student details, dates, duration, and college information
- Clean A4 layout with proper margins, header, and footer
- PDF export (wkhtmltopdf or compatible engines)
- Simple admin interface to review requests and generate letters
- Static assets for JNPA logos, fonts, and pattern images

---

## Project Structure

```

jnpa-internship-letter-generator/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
│
├── static/
│   ├── fonts/
│   └── img/
│
├── templates/
│   ├── admin.html
│   ├── form.html
│   ├── internship_letter.html
│   ├── login.html
│   └── view_request.html
│
├── uploads/
└── generated_letters/   (PDF output folder)

````

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/jnpa-internship-letter-generator.git
cd jnpa-internship-letter-generator
````

### 2. Create and activate a virtual environment

#### Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install wkhtmltopdf

This is required for PDF generation.

* Windows / macOS / Linux installers:
  [https://wkhtmltopdf.org/downloads.html](https://wkhtmltopdf.org/downloads.html)

Ensure `wkhtmltopdf` is added to your system PATH.

---

## Running the Application

### 1. Set environment variables (optional)

```bash
set FLASK_APP=app.py       # Windows
export FLASK_APP=app.py    # macOS / Linux
```

### 2. Start the Flask server

```bash
flask run
```

### 3. Open in browser

```
http://127.0.0.1:5000
```

---

## PDF Output

Generated internship letters will be saved inside:

```
generated_letters/
```

This folder is ignored in version control.

---

## Notes

* Do NOT upload Firebase keys, `.env`, PDFs, or virtual environment folders to GitHub.
* Devanagari fonts should be placed in `static/fonts/`.
* Images like the JNPA logo must be stored in `static/img/`.

---

## License

This project is for educational and internal use.

```


