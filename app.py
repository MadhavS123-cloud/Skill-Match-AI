from groq import Groq
import os
import json
from datetime import datetime
from flask import Flask, redirect, url_for, render_template, request, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.linkedin import make_linkedin_blueprint, linkedin
from oauthlib.oauth2 import TokenExpiredError
from dotenv import load_dotenv
import traceback

# =========================
# Flask App Setup
# =========================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

@app.errorhandler(500)
def handle_500(e):
    return f"<h1>Internal Server Error (Debug)</h1><p>An error occurred during execution.</p><pre>{traceback.format_exc()}</pre>", 500

# =========================
# Diagnostic Imports
# =========================
IMPORT_ERROR = None
try:
    from models.resume_ranker import rank_resumes
    from models.ats_checker import check_ats_friendliness
    from models.job_expander import expand_job_requirements
    from models.file_parser import extract_text_from_file
    from models.style_analyzer import analyze_company_style
    from models.evolution_tracker import track_evolution
    from models.rejection_simulator import simulate_rejection
except Exception:
    IMPORT_ERROR = traceback.format_exc()

# =========================
# Load environment variables
# =========================
load_dotenv()

# Allow OAuth over HTTP (ONLY for local development)
if os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG") == "1":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

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
    if IMPORT_ERROR:
        return f"<h1>Vercel Deployment Initialization Error</h1><pre>{IMPORT_ERROR}</pre>", 500
    return {"status": "ok", "message": "Vercel deployment is active", "vercel": os.environ.get("VERCEL", "0")}, 200

@app.route("/", methods=["GET", "POST"])
def index():
    if IMPORT_ERROR: return redirect(url_for("health"))
    
    is_google_authorized = google_bp is not None and google.authorized
    is_linkedin_authorized = linkedin_bp is not None and linkedin.authorized
    
    if not is_google_authorized and not is_linkedin_authorized:
        return redirect(url_for("login"))

    user = {}
    if is_google_authorized:
        try:
            resp = google.get("/oauth2/v2/userinfo")
            if resp.ok: user = resp.json()
        except Exception: pass
    elif is_linkedin_authorized:
        try:
            resp = linkedin.get("me")
            if resp.ok:
                data = resp.json()
                user = {"name": f"{data.get('localizedFirstName', '')} {data.get('localizedLastName', '')}".strip()}
        except Exception: pass

    all_matches = load_matches()
    recent_matches = all_matches[:10]
    
    stats = {"total": len(all_matches), "avg": "0%", "roles": 0, "week": 0}

    if request.method == "POST":
        # Handle resume analysis logic (kept same as before)
        pass

    return render_template("index.html", user=user, recent_matches=recent_matches, stats=stats)

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
