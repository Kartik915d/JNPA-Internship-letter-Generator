# 🚢 JNPA Internship Letter Generator

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Flask](https://img.shields.io/badge/Framework-Flask-green) ![License](https://img.shields.io/badge/License-Internal_Use-orange)

A specialized Flask-based web application designed to automate the generation of **official Internship Permission Letters** for the **Jawaharlal Nehru Port Authority (JNPA)**.

This tool streamlines the administrative process by generating bilingual (Hindi + English) letters with precise A4 formatting, correct Devanagari font rendering, and instant PDF export capabilities.

---

## ✨ Key Features

* **📄 PDF Automation:** Generates high-quality, printable PDFs using `wkhtmltopdf`.
* **🇮🇳 Bilingual Support:** Full support for Devanagari script (Hindi) alongside English.
* **📐 Precision Layout:** Custom A4 CSS styling with correct margins for official headers/footers.
* **📝 Form Automation:** Auto-fills student details, reference numbers, and dates.
* **🛠️ Admin Dashboard:** Simple interface to review requests and generate documents.
* **🗂️ Static Asset Management:** Handles official logos and custom fonts securely.

---

## 📁 Project Structure

```text
jnpa-internship-letter-generator/
│
├── app.py                   # Main Flask application entry point
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
├── .gitignore               # Git ignore rules
│
├── static/
│   ├── fonts/               # .ttf files (e.g., NotoSansDevanagari)
│   ├── css/                 # Custom styles for the web view
│   └── img/                 # JNPA Logos and signatures
│
├── templates/
│   ├── admin.html           # Admin dashboard
│   ├── form.html            # Student input form
│   ├── internship_letter.html # The HTML template for the PDF
│   └── login.html           # Admin authentication
│
├── uploads/                 # Temporary storage for user docs (ignored by git)
└── generated_letters/       # Output folder for PDFs (ignored by git)
````

-----

## ⚙️ Installation & Setup

### 1\. System Prerequisite (Crucial)

This project requires **`wkhtmltopdf`** to convert HTML to PDF. This is a system-level binary, not just a Python package.

  * **Windows:** Download the installer from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html).
      * *Note:* After installing, add the `bin` folder (e.g., `C:\Program Files\wkhtmltopdf\bin`) to your System PATH variables.
  * **Linux (Debian/Ubuntu):**
    ```bash
    sudo apt-get update
    sudo apt-get install wkhtmltopdf
    ```
  * **macOS:**
    ```bash
    brew install --cask wkhtmltopdf
    ```

### 2\. Clone the Repository

```bash
git clone [https://github.com/your-username/jnpa-internship-letter-generator.git](https://github.com/your-username/jnpa-internship-letter-generator.git)
cd jnpa-internship-letter-generator
```

### 3\. Set up Virtual Environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4\. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5\. Configuration

Ensure you have the required fonts. Download a Hindi-supporting font (like **Noto Sans Devanagari**) and place the `.ttf` file in:
`static/fonts/NotoSansDevanagari-Regular.ttf`

### 6\. Run the Application

```bash
# Set Flask app environment variable
export FLASK_APP=app.py  # macOS/Linux
set FLASK_APP=app.py     # Windows CMD
$env:FLASK_APP = "app.py" # Windows PowerShell

# Run
flask run
```

Access the app at: `http://127.0.0.1:5000`

-----

## 🔧 Troubleshooting & Tips

### 1\. Hindi Characters appear as squares (□□□)

This usually happens if `wkhtmltopdf` cannot find the font file on the server.

  * **Solution:** In `internship_letter.html`, use absolute system paths for the `@font-face` URL, or ensure the `.ttf` file is physically present in `static/fonts/`.

### 2\. `wkhtmltopdf` not found error

  * **Solution:** If using `pdfkit` in Python, you may need to manually point to the binary configuration in `app.py`:
    ```python
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    pdfkit.from_string(html, 'out.pdf', configuration=config)
    ```

### 3\. CSS not loading in PDF

  * **Solution:** PDF generators often struggle with external CSS sheets. It is best practice to include your CSS inside `<style>` tags directly within the `internship_letter.html` template.

-----

## 🤝 Contributing

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

-----

## 🧾 License

This project is intended for **internal and educational use** at JNPA.

```
```
