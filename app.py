from flask import Flask, render_template, request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import PyPDF2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

def preprocess_text(text):
    # Basic cleanup
    return text.strip()

def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def rank_resumes(job_desc, resumes_data):
    """
    resumes_data: list of dicts -> [{'name': 'filename or #1', 'content': 'full text'}]
    """
    if not job_desc or not resumes_data:
        return []
    
    # We need a list of just the text content for vectorization
    resumes_content = [r['content'] for r in resumes_data]
    
    # Corpus = Job Desc + All Resumes
    documents = [job_desc] + resumes_content
    
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        # returns empty if no valid words
        return []
    
    # Calculate cosine similarity between Job Desc (index 0) and Resumes (index 1 to end)
    # tfidf_matrix[0:1] is the job desc vector
    # tfidf_matrix[1:] involves all resume vectors
    if tfidf_matrix.shape[0] < 2:
        return []

    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    
    results = []
    for i, score in enumerate(cosine_sim):
        resume_name = resumes_data[i].get('name', f"Resume #{i+1}")
        content_preview = resumes_data[i]['content'][:100].replace('\n', ' ') + "..."
        
        results.append({
            "resume_no": resume_name,
            "score": round(score * 100, 2),
            "content": content_preview
        })
    
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    if request.method == "POST":
        job_description = request.form.get("job_description")
        
        # 1. Handle Text Area Input
        resumes_text_input = request.form.get("resumes_text", "")
        # Assuming double newline separation for pasted text
        parsed_resumes = []
        if resumes_text_input:
            chunks = resumes_text_input.split('\n\n')
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    parsed_resumes.append({
                        "name": f"Pasted Resume #{i+1}",
                        "content": chunk.strip()
                    })

        # 2. Handle File Uploads
        uploaded_files = request.files.getlist("resume_files")
        for file in uploaded_files:
            if file.filename == '':
                continue
            
            content = ""
            if file.filename.endswith('.pdf'):
                content = extract_text_from_pdf(file)
            elif file.filename.endswith('.txt'):
                content = file.read().decode('utf-8', errors='ignore')
            
            if content.strip():
                parsed_resumes.append({
                    "name": file.filename,
                    "content": content.strip()
                })

        if job_description and parsed_resumes:
            results = rank_resumes(job_description, parsed_resumes)

    return render_template(
        "index.html",
        results=results
    )

if __name__ == "__main__":
    app.run(debug=True, port=5001)
