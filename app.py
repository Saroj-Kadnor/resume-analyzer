from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import fitz  # PyMuPDF
import os
from azure.storage.blob import BlobServiceClient # --- IMPORT THIS ---

app = Flask(__name__)
CORS(app) # This allows your frontend (port 5500) to talk to your backend (port 5000)

# --- AZURE BLOB STORAGE CONFIG ---
# This will be None when you run locally, and that's OK now.
AZURE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
# Make sure this matches your container name
AZURE_CONTAINER_NAME = "resumes" 

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

    # Read the file content into a variable.
    file_content = file.read()
    
    # Reset the stream position for PyMuPDF to read it
    file.seek(0) 

    # --- START OF UPDATED LOGIC ---
    # We will only try to upload if the connection string is present
    if AZURE_CONNECTION_STRING:
        try:
            # Create a blob client using the connection string
            blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
            
            # Get a client to interact with the specific blob (file)
            blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=file.filename)
            
            print(f"Uploading {file.filename} to container {AZURE_CONTAINER_NAME}...")
            
            # Upload the file content to Azure Blob Storage
            blob_client.upload_blob(file_content, overwrite=True)
            print("Upload successful.")
            
        except Exception as e:
            # If upload fails, log it and continue
            print(f"Error uploading to Azure Blob Storage: {e}")
    else:
        # This will run when you test locally
        print("AZURE_STORAGE_CONNECTION_STRING not set. Skipping blob upload for local test.")
    # --- END OF UPDATED LOGIC ---

    # Extract text from PDF using PyMuPDF (using the file_content variable)
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        resume_text = ""
        for page in doc:
            resume_text += page.get_text()
    except Exception as e:
        print(f"Error reading PDF: {e}") # Added a print for debugging
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

