from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import fitz  # PyMuPDF
import os
app = Flask(__name__)
CORS(app)

# Predefined keywords for each job role
JOB_KEYWORDS = {
    "frontend": [
        "html", "css", "javascript", "react", "bootstrap", "tailwind", "typescript", "redux", "webpack", "ui/ux", "git", "cloud computing"
    ],
    "backend": [
        "python", "django", "flask", "sql", "api", "rest", "mongodb", "node.js", "express", "docker", "git", "cloud computing"
    ],
     "data": [
        "python", "pandas", "excel", "statistics", "machine learning", "numpy", "scikit-learn", "data visualization", "power bi", "sql", "cloud computing"
    ]
}
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    file = request.files.get('resume')
    job = request.form.get('job')

    if not file or not job:
        return jsonify({"error": "Missing resume file or job role"}), 400

    # Extract text from PDF using PyMuPDF
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        resume_text = ""
        for page in doc:
            resume_text += page.get_text()
    except Exception as e:
        return jsonify({"error": "Failed to read PDF"}), 500

    # Get keywords for selected job
    keywords = JOB_KEYWORDS.get(job.lower(), [])
    if not keywords:
        return jsonify({"error": "Invalid job role"}), 400

    # Score calculation
    matched = [word for word in keywords if word.lower() in resume_text.lower()]
    missing = [word for word in keywords if word.lower() not in resume_text.lower()]
    score = int((len(matched) / len(keywords)) * 100) if keywords else 0

    # Send result
    return jsonify({
        "matched_role": job,
        "score": score,
        "missing_skills": missing
    })

if __name__ == '__main__':
    app.run(debug=True)
