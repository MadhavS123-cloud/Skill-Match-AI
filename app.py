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
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
except ImportError:
    try:
        from werkzeug.contrib.fixers import ProxyFix
    except ImportError:
        ProxyFix = None
    except Exception:
        ProxyFix = None

# Import models
from models.resume_ranker import rank_resumes
from models.ats_checker import check_ats_friendliness
from models.job_expander import expand_job_requirements
from models.file_parser import extract_text_from_file
from models.style_analyzer import analyze_company_style
from models.evolution_tracker import track_evolution
from models.rejection_simulator import simulate_rejection
from models.salary_simulator import estimate_salary
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
print(f"Flask app instance created: {__name__}")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

# Enable ProxyFix for deployment (Render/Heroku/Vercel)
if ProxyFix:
    try:
        # Modern Werkzeug (0.15+)
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
    except TypeError:
        # Older Werkzeug
        try:
            app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=1)
        except Exception as e:
            print(f"WARNING: Failed to apply legacy ProxyFix: {e}")
    print("DEBUG: ProxyFix applied for production environment.")
else:
    print("WARNING: ProxyFix could not be imported. URL generation might be incorrect in production.")

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

# AI Setup (Local Models)
# All AI calls are now handled within their respective model modules using local engines.

# =========================
# OAuth Blueprints & Session Population
# =========================
# =========================
# User Management (JSON Storage)
# =========================
def get_users_file():
    if os.environ.get("VERCEL"):
        return "/tmp/users_data.json"
    return os.path.join(os.path.dirname(__file__), 'users_data.json')

def load_users():
    users_file = get_users_file()
    try:
        if os.path.exists(users_file):
            with open(users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading users: {e}")
    return {}

def save_user(user_profile):
    users = load_users()
    email = user_profile.get("email")
    if email:
        users[email] = user_profile
        users_file = get_users_file()
        try:
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2)
        except Exception as e:
            print(f"Error saving user: {e}")

# =========================
# OAuth Blueprints Configuration
# =========================
from flask_dance.consumer import oauth_authorized, oauth_error

google_id = os.getenv("GOOGLE_CLIENT_ID")
google_secret = os.getenv("GOOGLE_CLIENT_SECRET")
google_bp = make_google_blueprint(
    client_id=google_id,
    client_secret=google_secret,
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
    offline=True,
    reprompt_consent=True,
    authorized_url="/callback"
)
app.register_blueprint(google_bp, url_prefix="/auth/google")

linkedin_id = os.getenv("LINKEDIN_CLIENT_ID")
linkedin_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
linkedin_bp = make_linkedin_blueprint(
    client_id=linkedin_id,
    client_secret=linkedin_secret,
    scope=["openid", "profile", "email"],
    authorized_url="/callback"
)
app.register_blueprint(linkedin_bp, url_prefix="/auth/linkedin")

github_id = os.getenv("GITHUB_CLIENT_ID")
github_secret = os.getenv("GITHUB_CLIENT_SECRET")
github_bp = make_github_blueprint(
    client_id=github_id,
    client_secret=github_secret,
    authorized_url="/callback"
)
app.register_blueprint(github_bp, url_prefix="/auth/github")

# =========================
# Unified Authorized Handler
# =========================
def unified_auth_handler(blueprint, token, provider_name):
    from flask import flash
    if not token:
        flash(f"Failed to login with {provider_name.capitalize()}.", "error")
        return None

    user_info = {}
    try:
        if provider_name == "google":
            resp = blueprint.session.get("/oauth2/v2/userinfo")
            if resp.ok:
                data = resp.json()
                user_info = {
                    "name": data.get("name"),
                    "email": data.get("email"),
                    "image": data.get("picture"),
                    "provider": "google"
                }
        
        elif provider_name == "linkedin":
            resp = blueprint.session.get("https://api.linkedin.com/openid/userinfo")
            if resp.ok:
                data = resp.json()
                user_info = {
                    "name": data.get("name") or f"{data.get('given_name', '')} {data.get('family_name', '')}".strip(),
                    "email": data.get("email"),
                    "image": data.get("picture"),
                    "provider": "linkedin"
                }
        
        elif provider_name == "github":
            resp = blueprint.session.get("/user")
            if resp.ok:
                data = resp.json()
                # Secondary check for email if not public
                email = data.get("email")
                if not email:
                    emails_resp = blueprint.session.get("/user/emails")
                    if emails_resp.ok:
                        emails = emails_resp.json()
                        email = next((e["email"] for e in emails if e["primary"]), emails[0]["email"] if emails else None)
                
                user_info = {
                    "name": data.get("name") or data.get("login"),
                    "email": email,
                    "image": data.get("avatar_url"),
                    "provider": "github"
                }

    except Exception as e:
        flash(f"Error fetching user data from {provider_name.capitalize()}.", "error")
        print(f"Error fetching user info from {provider_name}: {e}")
        return None

    if not user_info.get("email"):
        flash(f"{provider_name.capitalize()} did not provide an email address. Please ensure your email is public or verified.", "error")
        return None

    # Check for duplicate email with different provider
    users = load_users()
    existing_user = users.get(user_info["email"])
    if existing_user and existing_user.get("provider") != provider_name:
        flash(f"An account with this email already exists via {existing_user.get('provider').capitalize()}. Please use that instead.", "error")
        return None

    # Store in session
    session["user_name"] = user_info["name"]
    session["user_email"] = user_info["email"]
    session["user_image"] = user_info["image"]
    session["auth_provider"] = user_info["provider"]
    session.permanent = True

    # Persist user profile
    save_user(user_info)
    return user_info

# Connect signals
@oauth_authorized.connect_via(google_bp)
def google_authorized(blueprint, token):
    if not unified_auth_handler(blueprint, token, "google"):
        return redirect(url_for("login"))

@oauth_authorized.connect_via(linkedin_bp)
def linkedin_authorized(blueprint, token):
    if not unified_auth_handler(blueprint, token, "linkedin"):
        return redirect(url_for("login"))

@oauth_authorized.connect_via(github_bp)
def github_authorized(blueprint, token):
    if not unified_auth_handler(blueprint, token, "github"):
        return redirect(url_for("login"))

@oauth_error.connect
def oauth_error_handler(blueprint, message, response):
    print(f"OAuth Error from {blueprint.name}: {message}")
    from flask import flash
    flash(f"Authentication failed: {message}", "error")

# =========================
# Auth Helpers
# =========================
def get_current_user():
    email = session.get("user_email")
    if email:
        # Try to load from "database" for most up-to-date info
        users = load_users()
        if email in users:
            return users[email]
        # Fallback to session
        return {
            "name": session.get("user_name"),
            "email": email,
            "image": session.get("user_image"),
            "provider": session.get("auth_provider")
        }
    
    if session.get("guest_user"):
        guest_id = session.get("guest_id", "anonymous")
        return {
            "name": session.get("custom_name") or f"Guest ({guest_id[:4]})",
            "email": f"guest_{guest_id}@local",
            "image": None,
            "provider": "guest"
        }
    return None

# =========================
# Template Context Processor
# =========================
@app.context_processor
def inject_globals():
    return {
        "google_enabled": bool(google_id and google_secret),
        "linkedin_enabled": bool(linkedin_id and linkedin_secret),
        "github_enabled": bool(github_id and github_secret),
        "current_user": get_current_user()
    }

# =========================
# Auth Decorator
# =========================
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

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
    
    # Handle redirect back to original page
    next_url = session.pop("next_url", None)
    return redirect(next_url or url_for("index"))

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Handle post-auth redirect if present
    next_url = session.pop("next_url", None)
    if next_url and next_url != request.path and next_url != request.url:
        print(f"DEBUG: Redirecting to saved next_url: {next_url}")
        return redirect(next_url)

    user = get_current_user()
    user_email = user.get("email")

    all_matches = load_matches()
    # FILTERING: Ensure users only see their own data
    user_matches = [m for m in all_matches if m.get("user_email") == user_email]
    recent_matches = user_matches[:10]
    
    results = None
    error_message = None
    if request.method == "POST":
        print(f"DEBUG: POST request received for user: {user_email}")
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
                        "user_email": user_email,
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
@login_required
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
@login_required
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
        session["guest_user"] = False
        session["user_email"] = email
        session["user_name"] = email.split("@")[0].capitalize()
        session["auth_provider"] = "magic"
        session.permanent = True
        
        # Handle redirect back to original page
        next_url = session.pop("next_url", None)
        return redirect(next_url or url_for("index"))
    return redirect(url_for("login"))

@app.route("/signup")
def signup():
    if get_current_user():
        return redirect(url_for("index"))
    
    # Store requested next URL for redirection after auth
    next_url = request.args.get("next")
    if next_url:
        session["next_url"] = next_url
        
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Simple authentication simulation
        if email and password:
            session["user_email"] = email
            session["user_name"] = email.split("@")[0].capitalize()
            session["auth_provider"] = "email"
            session.permanent = True
            
            # Handle redirect back to original page
            next_url = session.pop("next_url", None)
            return redirect(next_url or url_for("index"))

    if get_current_user():
        return redirect(url_for("index"))
    
    # Store requested next URL for redirection after auth
    next_url = request.args.get("next")
    if next_url:
        session["next_url"] = next_url
        
    return render_template("login.html")

@app.route("/google-login")
def google_login():
    next_url = request.args.get("next")
    if next_url: session["next_url"] = next_url
    return redirect(url_for("google.login"))

@app.route("/github-login")
def github_login():
    next_url = request.args.get("next")
    if next_url: session["next_url"] = next_url
    return redirect(url_for("github.login"))

@app.route("/linkedin-login")
def linkedin_login():
    next_url = request.args.get("next")
    if next_url: session["next_url"] = next_url
    return redirect(url_for("linkedin.login"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    data = request.json
    new_name = data.get("name")
    new_role = data.get("role")
    
    user = get_current_user()
    if user:
        if new_name:
            user["name"] = new_name
            session["user_name"] = new_name
        if new_role is not None:
            user["role"] = new_role
            session["user_role"] = new_role
            
        save_user(user)
        return jsonify({"status": "success", "user": user})
    
    return jsonify({"status": "error", "message": "User not found"}), 404

@app.route("/toggle-setting", methods=["POST"])
@login_required
def toggle_setting():
    data = request.json
    setting = data.get("setting")
    value = data.get("value")
    if setting is not None:
        session[setting] = value
        return jsonify({"status": "success", setting: value})
    return jsonify({"status": "error", "message": "Setting name is required"}), 400

@app.route("/simulate-salary", methods=["POST"])
@login_required
def simulate_salary_route():
    data = request.json
    role = data.get("role")
    company = data.get("company")
    location = data.get("location")
    experience = data.get("experience")
    score = data.get("score")
    education = data.get("education", "")
    seniority = data.get("seniority", "")
    
    if not all([role, company, location, experience, score]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
        
    try:
        result = estimate_salary(role, company, location, experience, score, education, seniority)
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    # Bind to 0.0.0.0 to be accessible in containerized environments like Render
    print(f"Starting Skill Match AI on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
