from groq import Groq
import os
import json
from datetime import datetime
from flask import Flask, redirect, url_for, render_template, request, session, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.linkedin import make_linkedin_blueprint, linkedin
from flask_dance.contrib.github import make_github_blueprint, github
from oauthlib.oauth2 import TokenExpiredError
from dotenv import load_dotenv
import traceback
from werkzeug.middleware.proxy_fix import ProxyFix

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

# Always allow relaxed token scope to handle LinkedIn's extra scopes
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

# =========================
# Flask App Setup
# =========================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

# Enable ProxyFix for deployment (Render/Heroku/Vercel)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Only force HTTPS for URL generation in production
if os.getenv("FLASK_ENV") != "development" and os.getenv("FLASK_DEBUG") != "1":
    app.config["PREFERRED_URL_SCHEME"] = "https"

# Force HTTPS for cookies if not in development
if os.getenv("FLASK_ENV") != "development":
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

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
        offline=True,
        reprompt_consent=True,
        login_url="/google",
        authorized_url="/google/authorized"
    )
    app.register_blueprint(google_bp, url_prefix="/login")

linkedin_client_id = os.getenv("LINKEDIN_CLIENT_ID")
linkedin_client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
linkedin_bp = None
if linkedin_client_id and linkedin_client_secret:
    linkedin_bp = make_linkedin_blueprint(
        client_id=linkedin_client_id,
        client_secret=linkedin_client_secret,
        scope=["openid", "profile", "email"],
        login_url="/linkedin",
        authorized_url="/linkedin/authorized"
    )
    app.register_blueprint(linkedin_bp, url_prefix="/login")

github_client_id = os.getenv("GITHUB_CLIENT_ID")
github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
github_bp = None
if github_client_id and github_client_secret:
    github_bp = make_github_blueprint(
        client_id=github_client_id,
        client_secret=github_client_secret,
        login_url="/github",
        authorized_url="/github/authorized"
    )
    app.register_blueprint(github_bp, url_prefix="/login")

# =========================
# Template Context Processor
# =========================
@app.context_processor
def inject_auth_status():
    return {
        "google_enabled": google_bp is not None,
        "linkedin_enabled": linkedin_bp is not None,
        "github_enabled": github_bp is not None
    }

# =========================
# Routes
# =========================


@app.route("/health")
def health():
    return {"status": "ok", "message": "Skill Match AI service is active"}, 200

@app.route("/bypass-login")
def bypass_login():
    session["guest_user"] = True
    if "guest_id" not in session:
        import os
        session["guest_id"] = os.urandom(8).hex()
    return redirect(url_for("index"))

@app.route("/", methods=["GET", "POST"])
def index():
    is_guest = session.get("guest_user", False)
    is_google_authorized = google_bp is not None and google.authorized
    is_linkedin_authorized = linkedin_bp is not None and linkedin.authorized
    is_github_authorized = github_bp is not None and github.authorized
    
    if not any([is_google_authorized, is_linkedin_authorized, is_github_authorized, is_guest]):
        return redirect(url_for("login"))

    user = {
        "name": session.get("custom_name") or "Guest Candidate", 
        "email": "guest@example.com"
    }
    if is_google_authorized:
        try:
            resp = google.get("/oauth2/v2/userinfo")
            if resp.ok: 
                user_data = resp.json()
                user["name"] = user_data.get("name", "Guest")
                user["email"] = user_data.get("email", "")
        except Exception as e:
            print(f"Google OAuth info failed: {e}")
    elif is_linkedin_authorized:
        try:
            # Try OpenID Connect userinfo endpoint first (modern LinkedIn API)
            resp = linkedin.get("userinfo")
            if resp.ok:
                data = resp.json()
                user["name"] = data.get("name") or f"{data.get('given_name', '')} {data.get('family_name', '')}".strip() or "Guest"
                user["email"] = data.get("email", "")
                print(f"LinkedIn OIDC info success: {user['name']}")
            else:
                # Fallback to old profile endpoint if OIDC fails
                resp = linkedin.get("me")
                if resp.ok:
                    data = resp.json()
                    user["name"] = f"{data.get('localizedFirstName', '')} {data.get('localizedLastName', '')}".strip() or "Guest"
                    print(f"LinkedIn Legacy info success: {user['name']}")
                else:
                    print(f"LinkedIn OAuth failed both endpoints. Userinfo status: {resp.status_code}")
        except Exception as e:
            print(f"LinkedIn OAuth info failed: {e}")
            traceback.print_exc()
    elif is_github_authorized:
        try:
            resp = github.get("/user")
            if resp.ok:
                user_data = resp.json()
                user["name"] = user_data.get("name") or user_data.get("login", "Guest")
                user["email"] = user_data.get("email", "")
        except Exception as e:
            print(f"GitHub OAuth info failed: {e}")

    elif is_guest:
        guest_id = session.get("guest_id", "anonymous")
        user["name"] = session.get("custom_name") or f"Guest ({guest_id[:4]})"
        user["email"] = f"guest_{guest_id}@local"

    all_matches = load_matches()
    # FILTERING: Ensure users only see their own data
    user_email = user.get("email")
    user_matches = [m for m in all_matches if m.get("user_email") == user_email]
    recent_matches = user_matches[:10]
    
    results = None
    error_message = None
    if request.method == "POST":
        print(f"DEBUG: POST request received. Guest Mode: {is_guest}")
        job_title = request.form.get("job_title", "").strip()
        job_description = request.form.get("job_description", "").strip()
        
        if not job_description:
            error_message = "Job description is required."
        else:
            full_job_context = f"{job_title}\n{job_description}" if job_title else job_description
            
            raw_resumes = [r.strip() for r in request.form.get("resumes", "").split("\n\n") if r.strip()]
            uploaded_files = request.files.getlist("resume_files")
            for f in uploaded_files:
                if f.filename:
                    text = extract_text_from_file(f, f.filename)
                    if text: raw_resumes.append(text)
            
            print(f"DEBUG: Found {len(raw_resumes)} resumes to process.")
            
            if not raw_resumes:
                error_message = "Please paste a resume or upload a file."
            
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
                        "role_focus": ats_results.get("role_focus", "Professional"),
                        "missing_skills": ats_results.get("missing_skills", []),
                        "detailed_skills": ats_results.get("detailed_skills", []),
                        "experience_match": ats_results.get("experience_match", []),
                        "strengths": ats_results.get("strengths", []),
                        "areas_to_develop": ats_results.get("areas_to_develop", []),
                        "recommendation": ats_results.get("recommendation", ""),
                        "roadmap": ats_results.get("roadmap", []),
                        "risk_analysis": ats_results.get("risk_analysis", {"level": "Low", "findings": []}),
                        "feedback_loop": ats_results.get("feedback_loop", {}),
                        "sample_ideal_resume": ats_results.get("sample_ideal_resume", ""),
                        "content": raw_resumes[index],
                        "company_style_fit": style_analysis
                    }
                    
                    # Suggest Template
                    suggested_tpl = suggest_template(style_analysis)
                    analysis_result["suggested_template"] = suggested_tpl
                    
                    results.append(analysis_result)
                    
                    # Save to history with privacy association
                    new_match_entry = {
                        "user_email": user.get("email"),
                        "role": job_title or "Unnamed Role",
                        "candidate": f"Candidate {index + 1}",
                        "score": analysis_result['ats_score'],
                        "timestamp": datetime.now().isoformat(),
                        "full_analysis": analysis_result
                    }
                    all_matches.insert(0, new_match_entry)
                    user_matches.insert(0, new_match_entry)
                
                save_matches(all_matches)
                
                # Simple stats calculation for THIS user
                total_score = sum(m['score'] for m in user_matches if 'score' in m)
                avg_score = f"{round(total_score / len(user_matches), 1)}%" if user_matches else "0%"
                unique_roles = len(set(m['role'] for m in user_matches if 'role' in m))
                
                return render_template("index.html", 
                                     user=user, 
                                     results=results, 
                                     recent_matches=user_matches[:10], 
                                     stats={"total": len(user_matches), "avg": avg_score, "roles": unique_roles, "week": len(user_matches)},
                                     job_title=job_title,
                                     job_description=job_description,
                                     expanded_jd=was_expanded,
                                     error_message=error_message)

    # Initial stats for Get request (Filtered for privacy)
    total_score = sum(m['score'] for m in user_matches if 'score' in m)
    avg_score = f"{round(total_score / len(user_matches), 1)}%" if user_matches else "0%"
    unique_roles = len(set(m['role'] for m in user_matches if 'role' in m))
    
    return render_template("index.html", 
                           user=user, 
                           recent_matches=recent_matches, 
                           stats={"total": len(user_matches), "avg": avg_score, "roles": unique_roles, "week": len(user_matches)},
                           error_message=error_message)

@app.route("/rejection-simulator", methods=["POST"])
def rejection_simulator():
    data = request.json
    company = data.get("company")
    role = data.get("role")
    resume = data.get("resume")
    
    if not all([company, role, resume]):
        return jsonify({"status": "error", "error": "All fields are required"}), 400
        
    try:
        results = simulate_rejection(resume, company, role)
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        print(f"Simulation failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/modify-resume", methods=["GET", "POST"])
def modify_resume():
    # In-app editor for resume refinement
    resume_content = request.args.get("content", "")
    job_desc = request.args.get("jd", "")
    
    if request.method == "POST":
        resume_content = request.json.get("content")
        job_desc = request.json.get("jd")
        template = request.json.get("template")
        
        # Re-analyze live with template context
        ats_results = check_ats_friendliness(resume_content, job_desc, template=template)
        return jsonify(ats_results)

    templates = get_company_templates()
    return render_template("modify_resume.html", content=resume_content, jd=job_desc, templates=templates)

@app.route("/login/magic", methods=["POST"])
def login_magic():
    email = request.form.get("email")
    if email:
        session["guest_user"] = True
        session["guest_id"] = email.split("@")[0]
        return redirect(url_for("index"))
    return redirect(url_for("login"))

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/google-login")
def google_login():
    return redirect(url_for("google.login"))

@app.route("/github-login")
def github_login():
    return redirect(url_for("github.login"))

@app.route("/linkedin-login")
def linkedin_login():
    return redirect(url_for("linkedin.login"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/update-profile", methods=["POST"])
def update_profile():
    data = request.json
    new_name = data.get("name")
    if new_name:
        session["custom_name"] = new_name
        return jsonify({"status": "success", "name": new_name})
    return jsonify({"status": "error", "message": "Name is required"}), 400

@app.route("/toggle-setting", methods=["POST"])
def toggle_setting():
    data = request.json
    setting = data.get("setting")
    value = data.get("value")
    if setting is not None:
        session[setting] = value
        return jsonify({"status": "success", setting: value})
    return jsonify({"status": "error", "message": "Setting name is required"}), 400

if __name__ == "__main__":
    app.run(debug=True)
