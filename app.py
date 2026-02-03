from groq import Groq
import os
import json
from datetime import datetime
from flask import Flask, redirect, url_for, render_template, request, session, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.linkedin import make_linkedin_blueprint, linkedin
from oauthlib.oauth2 import TokenExpiredError
from dotenv import load_dotenv
import traceback

# Import models
from models.resume_ranker import rank_resumes
from models.ats_checker import check_ats_friendliness
from models.job_expander import expand_job_requirements
from models.file_parser import extract_text_from_file
from models.style_analyzer import analyze_company_style
from models.evolution_tracker import track_evolution
from models.rejection_simulator import simulate_rejection
from models.template_matcher import suggest_template, get_company_templates

# =========================
# Load environment variables
# =========================
load_dotenv()

# Allow OAuth over HTTP (ONLY for local development)
if os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG") == "1":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# =========================
# Flask App Setup
# =========================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

# =========================
# Persistent Storage (JSON file)
# =========================
def get_matches_file():
    if os.environ.get("VERCEL"):
        tmp_path = "/tmp/matches_data.json"
        if not os.path.exists(tmp_path):
            bundled_path = os.path.join(os.path.dirname(__file__), 'matches_data.json')
            return bundled_path if os.path.exists(bundled_path) else tmp_path
        return tmp_path
    else:
        return os.path.join(os.path.dirname(__file__), 'matches_data.json')

def load_matches():
    matches_file = get_matches_file()
    try:
        if os.path.exists(matches_file):
            with open(matches_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading matches: {e}")
    return []

def save_matches(matches):
    matches_file = "/tmp/matches_data.json" if os.environ.get("VERCEL") else get_matches_file()
    try:
        with open(matches_file, 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=2)
    except Exception as e:
        print(f"Error saving matches: {e}")

# =========================
# Groq AI Setup
# =========================
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception:
        return None

client = get_groq_client()
MODEL_NAME = "llama-3.3-70b-versatile"

# =========================
# OAuth Blueprints
# =========================
google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
google_bp = None
if google_client_id and google_client_secret:
    google_bp = make_google_blueprint(
        client_id=google_client_id,
        client_secret=google_client_secret,
        scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
        redirect_url="/google-callback",
    )
    app.register_blueprint(google_bp, url_prefix="/login")

linkedin_client_id = os.getenv("LINKEDIN_CLIENT_ID")
linkedin_client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
linkedin_bp = None
if linkedin_client_id and linkedin_client_secret:
    linkedin_bp = make_linkedin_blueprint(
        client_id=linkedin_client_id,
        client_secret=linkedin_client_secret,
        scope=["r_emailaddress", "r_liteprofile"],
    )
    app.register_blueprint(linkedin_bp, url_prefix="/login")

# =========================
# Routes
# =========================

@app.route("/health")
def health():
    return {"status": "ok", "message": "Vercel deployment is active"}, 200

@app.route("/", methods=["GET", "POST"])
def index():
    is_google_authorized = google_bp is not None and google.authorized
    is_linkedin_authorized = linkedin_bp is not None and linkedin.authorized
    
    if not is_google_authorized and not is_linkedin_authorized:
        return redirect(url_for("login"))

    user = {}
    if is_google_authorized:
        try:
            resp = google.get("/oauth2/v2/userinfo")
            if resp.ok: user = resp.json()
        except: pass
    elif is_linkedin_authorized:
        try:
            resp = linkedin.get("me")
            if resp.ok:
                data = resp.json()
                user = {"name": f"{data.get('localizedFirstName', '')} {data.get('localizedLastName', '')}".strip()}
        except: pass

    all_matches = load_matches()
    recent_matches = all_matches[:10]
    
    results = None
    if request.method == "POST":
        job_title = request.form.get("job_title", "").strip()
        job_description = request.form["job_description"]
        full_job_context = f"{job_title}\n{job_description}" if job_title else job_description
        
        raw_resumes = [r.strip() for r in request.form["resumes"].split("\n\n") if r.strip()]
        uploaded_files = request.files.getlist("resume_files")
        for f in uploaded_files:
            if f.filename:
                text = extract_text_from_file(f, f.filename)
                if text: raw_resumes.append(text)

        if raw_resumes:
            expanded_description, was_expanded = expand_job_requirements(full_job_context)
            process_description = expanded_description
            ranked_results = rank_resumes(raw_resumes, process_description)
            
            results = []
            for rank, (index, score_vec) in enumerate(ranked_results):
                score = round(float(score_vec[0]) * 100, 1)
                ats_results = check_ats_friendliness(raw_resumes[index], process_description)
                style_analysis = analyze_company_style(raw_resumes[index])
                
                analysis_result = {
                    "resume_no": index + 1,
                    "score": ats_results.get("score", 0),
                    "similarity_score": score,
                    "ats_score": ats_results.get("score", 0),
                    "ats_summary": ats_results.get("summary", ""),
                    "missing_skills": ats_results.get("missing_skills", []),
                    "roadmap": ats_results.get("roadmap", []),
                    "risk_analysis": ats_results.get("risk_analysis", {"level": "Low", "findings": []}),
                    "content": raw_resumes[index],
                    "style_fit": style_analysis
                }
                
                # Suggest Template
                suggested_tpl = suggest_template(style_analysis)
                analysis_result["suggested_template"] = suggested_tpl
                
                results.append(analysis_result)
                
                # Save to history
                new_match_entry = {
                    "role": job_title or "Unnamed Role",
                    "candidate": f"Candidate {index + 1}",
                    "score": analysis_result['ats_score'],
                    "timestamp": datetime.now().isoformat(),
                    "full_analysis": analysis_result
                }
                all_matches.insert(0, new_match_entry)
            
            save_matches(all_matches)
            return render_template("index.html", user=user, results=results, recent_matches=recent_matches, stats={"total": len(all_matches), "avg": "0%", "roles": 0, "week": 0})

    return render_template("index.html", user=user, recent_matches=recent_matches, stats={"total": len(all_matches), "avg": "0%", "roles": 0, "week": 0})

@app.route("/modify-resume", methods=["GET", "POST"])
def modify_resume():
    # In-app editor for resume refinement
    resume_content = request.args.get("content", "")
    job_desc = request.args.get("jd", "")
    
    if request.method == "POST":
        resume_content = request.json.get("content")
        job_desc = request.json.get("jd")
        
        # Re-analyze live
        ats_results = check_ats_friendliness(resume_content, job_desc)
        return jsonify(ats_results)

    templates = get_company_templates()
    return render_template("modify_resume.html", content=resume_content, jd=job_desc, templates=templates)

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/google-login")
def google_login():
    if not google.authorized: return redirect(url_for("google.login"))
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
