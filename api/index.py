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
import sys

# Ensure api/models is available for import
sys.path.insert(0, os.path.dirname(__file__))

# =========================
# Flask App Setup
# =========================
# When running in Vercel, templates and static are in the root
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

@app.errorhandler(500)
def handle_500(e):
    return f"<h1>Internal Server Error (Vercel Debug)</h1><p>Initialization or runtime error.</p><pre>{traceback.format_exc()}</pre>", 500

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
            bundled_path = os.path.join(os.path.dirname(__file__), '..', 'matches_data.json')
            return bundled_path if os.path.exists(bundled_path) else tmp_path
        return tmp_path
    else:
        return os.path.join(os.path.dirname(__file__), '..', 'matches_data.json')

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
    
    is_google_authorized = google_bp is not None and google.authorized if 'google_bp' in globals() else False
    is_linkedin_authorized = linkedin_bp is not None and linkedin.authorized if 'linkedin_bp' in globals() else False
    
    if not is_google_authorized and not is_linkedin_authorized:
        return redirect(url_for("login"))

    user = {}
    # ... (simplified for now to test load)
    return render_template("index.html", user=user, recent_matches=[], stats={"total": 0, "avg": "0%", "roles": 0, "week": 0})

@app.route("/login")
def login():
    return render_template("login.html")

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

# LinkedIn setup omitted for brevity in this diagnostic version
# ...

# Vercel Handler
handler = app
