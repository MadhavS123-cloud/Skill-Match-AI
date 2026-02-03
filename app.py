from groq import Groq
import os
import json
from datetime import datetime
from flask import Flask, redirect, url_for, render_template, request, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.linkedin import make_linkedin_blueprint, linkedin
from oauthlib.oauth2 import TokenExpiredError
from dotenv import load_dotenv

from models.resume_ranker import rank_resumes
from models.ats_checker import check_ats_friendliness
from models.job_expander import expand_job_requirements
from models.file_parser import extract_text_from_file
from models.style_analyzer import analyze_company_style
from models.evolution_tracker import track_evolution
from models.rejection_simulator import simulate_rejection

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
# Vercel has a read-only filesystem except for /tmp
def get_matches_file():
    if os.environ.get("VERCEL"):
        tmp_path = "/tmp/matches_data.json"
        # If tmp eye doesn't exist, check if we have a bundled version to seed from
        if not os.path.exists(tmp_path):
            bundled_path = os.path.join(os.path.dirname(__file__), 'matches_data.json')
            return bundled_path if os.path.exists(bundled_path) else tmp_path
        return tmp_path
    else:
        return os.path.join(os.path.dirname(__file__), 'matches_data.json')

def load_matches():
    """Load all matches from persistent storage"""
    matches_file = get_matches_file()
    try:
        if os.path.exists(matches_file):
            with open(matches_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading matches from {matches_file}: {e}")
    return []

def save_matches(matches):
    """Save matches to persistent storage"""
    # On Vercel, we can only write to /tmp
    matches_file = "/tmp/matches_data.json" if os.environ.get("VERCEL") else get_matches_file()
    try:
        with open(matches_file, 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=2)
    except Exception as e:
        print(f"Error saving matches to {matches_file}: {e}")

# =========================
# Groq AI Setup
# =========================
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("WARNING: GROQ_API_KEY not found. Some features will be disabled.")
        return None
    try:
        return Groq(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return None

client = get_groq_client()
MODEL_NAME = "llama-3.3-70b-versatile"

# =========================
# Google OAuth Blueprint
# =========================
google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

if google_client_id and google_client_secret:
    google_bp = make_google_blueprint(
        client_id=google_client_id,
        client_secret=google_client_secret,
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        redirect_url="/google-callback",
    )
    app.register_blueprint(google_bp, url_prefix="/login")
else:
    print("WARNING: Google OAuth credentials missing. Google Login disabled.")
    google_bp = None

# =========================
# LinkedIn OAuth Blueprint
# =========================
linkedin_client_id = os.getenv("LINKEDIN_CLIENT_ID")
linkedin_client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")

if linkedin_client_id and linkedin_client_secret:
    linkedin_bp = make_linkedin_blueprint(
        client_id=linkedin_client_id,
        client_secret=linkedin_client_secret,
        scope=["r_emailaddress", "r_liteprofile"],
    )
    app.register_blueprint(linkedin_bp, url_prefix="/login")
else:
    print("WARNING: LinkedIn OAuth credentials missing. LinkedIn Login disabled.")
    linkedin_bp = None

# =========================
# Routes
# =========================

@app.route("/health")
def health():
    return {"status": "ok", "message": "Vercel deployment is active"}, 200

@app.route("/", methods=["GET", "POST"])
def index():
    # Fix: Check if blueprints exist before checking authorization
    is_google_authorized = google_bp is not None and google.authorized
    is_linkedin_authorized = linkedin_bp is not None and linkedin.authorized
    
    if not is_google_authorized and not is_linkedin_authorized:
        return redirect(url_for("login"))

    user = {}
    
    if is_google_authorized:
        try:
            resp = google.get("/oauth2/v2/userinfo")
        except TokenExpiredError:
            return redirect(url_for("google.login"))

        if not resp.ok:
            return redirect(url_for("google.login"))

        user = resp.json()
    
    elif is_linkedin_authorized:
        try:
            resp = linkedin.get("me")
        except TokenExpiredError:
            return redirect(url_for("linkedin.login"))
            
        if not resp.ok:
            return redirect(url_for("linkedin.login"))
            
        data = resp.json()
        first_name = data.get("localizedFirstName", "User")
        last_name = data.get("localizedLastName", "")
        # Try to get profile picture
        picture = ""
        if "profilePicture" in data and "displayImage~" in data["profilePicture"]:
             elements = data["profilePicture"]["displayImage~"].get("elements", [])
             if elements and len(elements) > 0:
                 identifiers = elements[-1].get("identifiers", [])
                 if identifiers:
                     picture = identifiers[0].get("identifier", "")

        user = {
            "name": f"{first_name} {last_name}".strip(),
            "picture": picture,
            "email": "LinkedIn User" # Getting email requires a separate complex call, skipping for simplicity in this view
        }

    # Get recent matches from PERSISTENT storage (not session)
    all_matches = load_matches()
    recent_matches = all_matches[:10]  # Show last 10 in dashboard
    
    # Calculate REAL Dashboard Metrics (no fake numbers)
    total_matches = len(all_matches)
    
    # Use safe sum/calculation to avoid TypeError if 'score' is missing or not a number
    try:
        scores = [float(m.get('score', 0)) for m in all_matches if m.get('score') is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    except (TypeError, ValueError, ZeroDivisionError):
        avg_score = 0
        
    active_roles = len(set(str(m.get('role', 'Unknown')) for m in all_matches))
    
    # Count matches from this week (last 7 days)
    from datetime import timedelta
    week_ago = datetime.now() - timedelta(days=7)
    matches_this_week = 0
    for m in all_matches:
        try:
            date_str = m.get('timestamp', '')
            if date_str:
                match_date = datetime.fromisoformat(date_str)
                if match_date >= week_ago:
                    matches_this_week += 1
            else:
                legacy_date = str(m.get('date', '')).lower()
                if "now" in legacy_date or "today" in legacy_date:
                    matches_this_week += 1
        except Exception:
            continue
    
    stats = {
        "total": total_matches,
        "avg": f"{avg_score}%" if total_matches > 0 else "0%",
        "roles": active_roles,
        "week": matches_this_week
    }
    
    results = None

    if request.method == "POST":
        job_title = request.form.get("job_title", "").strip()
        job_description = request.form["job_description"]
        
        # Combine title and description for better matching if title is provided
        full_job_context = f"{job_title}\n{job_description}" if job_title else job_description
        # 1. Collect pasted resumes
        raw_resumes = [r.strip() for r in request.form["resumes"].split("\n\n") if r.strip()]
        
        # 2. Collect uploaded resumes
        uploaded_files = request.files.getlist("resume_files")
        for f in uploaded_files:
            if f.filename:
                text = extract_text_from_file(f, f.filename)
                if text:
                    raw_resumes.append(text)

        if raw_resumes:
            # Automatically expand short job titles into full requirements
            expanded_description, was_expanded = expand_job_requirements(full_job_context)
            process_description = expanded_description # Use expanded for matching
            
            ranked_results = rank_resumes(raw_resumes, process_description)
            
            results = []
            for rank, (index, score_vec) in enumerate(ranked_results):
                score = round(float(score_vec[0]) * 100, 1)
                ats_results = check_ats_friendliness(raw_resumes[index], process_description)
                
                # NEW: Company Style Analysis
                style_analysis = analyze_company_style(raw_resumes[index])
                
                # Top 10% Logic: Score > 90 or Rank 1 in a pool
                is_top_tier = score >= 90 or (rank == 0 and len(ranked_results) > 1)
                
                # Get Matched and Missing skills directly from AI for consistency
                detailed_skills = ats_results.get("matched_skills", [])
                missing_skills = ats_results.get("missing_skills", [])
                
                # If AI failed to provide matched skills, provide a sensible empty state
                if not detailed_skills:
                    detailed_skills = []

                strengths = ats_results.get("roadmap", ["Experience Alignment", "Technical keyword consistency"])[:3]
                areas_to_develop = ats_results.get("tips", ["Quantify projectile impacts", "Mention industry-standard tools"])[:2]
                
                experience_match = [
                    {"label": "Experience Alignment", "candidate": "Found", "required": "High", "pct": 90 if score > 70 else 60},
                    {"label": "Role Fit", "candidate": "Relevant", "required": "Optimal", "pct": score}
                ]

                results.append({
                    "resume_no": index + 1,
                    "score": ats_results.get("score", 0), # Primary score is now the AI analysis
                    "similarity_score": score, # Keep TF-IDF as secondary insight
                    "ats_score": ats_results.get("score", 0),
                    "ats_summary": ats_results.get("summary", ""),
                    "ats_tips": ats_results.get("tips", []),
                    "missing_skills": missing_skills,
                    "roadmap": ats_results.get("roadmap", []),
                    "role_focus": ats_results.get("role_focus", ""),
                    "risk_analysis": ats_results.get("risk_analysis", {"level": "Low", "findings": [], "skepticism_reason": ""}),
                    "is_top_tier": is_top_tier,
                    "strengths": strengths,
                    "areas_to_develop": areas_to_develop,
                    "detailed_skills": detailed_skills,
                    "experience_match": experience_match,
                    "recommendation": ats_results.get("recommendation", "Consider an interview to assess soft skills and cultural fit."),
                    "content": raw_resumes[index][:200] + "...",
                    # NEW: Feedback Loop data
                    "feedback_loop": ats_results.get("feedback_loop", {
                        "current_percentile": 50,
                        "gap_to_top_10": 40,
                        "sections_to_improve": [],
                        "quick_wins": [],
                        "major_upgrades": []
                    }),
                    "improvement_priority": ats_results.get("improvement_priority", []),
                    # NEW: Company Style Fit data
                    "company_style_fit": {
                        "best_fit": style_analysis.get("best_fit_culture", "Unknown"),
                        "fit_score": style_analysis.get("fit_score", 0),
                        "summary": style_analysis.get("style_summary", ""),
                        "culture_breakdown": style_analysis.get("culture_match_breakdown", {}),
                        "style_details": style_analysis.get("style_analysis", {}),
                        "top_improvements": style_analysis.get("top_style_improvements", [])
                    }
                })

            # Save to PERSISTENT storage (not just session)
            for r in results:
                # Find previous match for this role to track evolution
                previous_match = next((m for m in all_matches if m.get('role') == (job_title if job_title else "Unnamed Role")), None)
                
                evolution_data = None
                if previous_match and 'full_analysis' in previous_match:
                    evolution_data = track_evolution(previous_match['full_analysis'], r)

                new_match_entry = {
                    "role": job_title if job_title else "Unnamed Role",
                    "candidate": f"Candidate {r['resume_no']}",
                    "score": r['ats_score'], # Use AI score for persistent history
                    "date": "Just now",
                    "timestamp": datetime.now().isoformat(),
                    "full_analysis": r, # Store full analysis for future comparisons
                    "evolution": evolution_data # Store current evolution signal
                }
                all_matches.insert(0, new_match_entry)
                
                # Update the result object with evolution data for frontend display
                r['evolution'] = evolution_data
            
            # Save to persistent file
            save_matches(all_matches)
            
            # Update metrics safely
            try:
                new_total = len(all_matches)
                new_scores = [float(m.get('score', 0)) for m in all_matches if m.get('score') is not None]
                new_avg = round(sum(new_scores) / len(new_scores), 1) if new_scores else 0
            except:
                new_avg = avg_score

            return render_template(
                "index.html",
                user=user,
                results=results,
                recent_matches=recent_matches,
                stats={
                    "total": len(all_matches),
                    "avg": f"{new_avg}%",
                    "roles": len(set(str(m.get('role', 'Unknown')) for m in all_matches)),
                    "week": stats['week'] + len(results)
                },
                expanded_jd=expanded_description if was_expanded else None
            )

    return render_template(
        "index.html",
        user=user,
        results=results,
        recent_matches=recent_matches,
        stats=stats
    )



@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/google-login")
def google_login():
    if google_bp is None:
        return "Google OAuth is not configured", 503
    if not google.authorized:
        return redirect(url_for("google.login"))
    return redirect(url_for("index"))


@app.route("/google-callback")
def google_callback():
    if google_bp is None:
        return "Google OAuth is not configured", 503
    if not google.authorized:
        return redirect(url_for("login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Failed to fetch user info", 400

    user_info = resp.json()
    session["user"] = {
        "name": user_info.get("name"),
        "email": user_info.get("email"),
        "picture": user_info.get("picture"),
    }

    return redirect(url_for("index"))


@app.route("/linkedin-callback")
def linkedin_callback():
    if linkedin_bp is None:
        return "LinkedIn OAuth is not configured", 503
    if not linkedin.authorized:
        return redirect(url_for("login"))
    
    # We could fetch user info here and store in session, but index() handles it.
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/chat", methods=["POST"])
def chat():
    # Fix: Check if blueprints exist before checking authorization
    is_google_authorized = google_bp is not None and google.authorized
    is_linkedin_authorized = linkedin_bp is not None and linkedin.authorized
    
    if not is_google_authorized and not is_linkedin_authorized:
        return {"error": "Unauthorized"}, 401
    
    user_message = request.json.get("message")
    if not user_message:
        return {"error": "No message provided"}, 400

    if not client:
        return {"error": "AI service is currently unavailable (missing API key)."}, 503

    try:
        # System instructions to keep the AI on-brand
        prompt = f"""
        You are 'Skill Match AI Assistant', a helpful career coach and platform guide.
        The user is currently using Skill Match AI, an app that ranks resumes against job descriptions.
        Keep your answers concise, helpful, and professional but modern (Gen Z friendly).
        If the user asks about the app, explain that it uses AI to calculate similarity scores between resumes and job requirements.
        
        User: {user_message}
        """
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a career coach assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return {"response": completion.choices[0].message.content}
    except Exception as e:
        error_msg = str(e)
        print(f"Error calling Groq: {error_msg}")
        return {"error": error_msg}, 500


@app.route("/rejection-simulator", methods=["POST"])
def rejection_simulator():
    # Fix: Check if blueprints exist before checking authorization
    is_google_authorized = google_bp is not None and google.authorized
    is_linkedin_authorized = linkedin_bp is not None and linkedin.authorized
    
    if not is_google_authorized and not is_linkedin_authorized:
        return {"error": "Unauthorized"}, 401
    
    data = request.json
    company = data.get("company", "").strip()
    role = data.get("role", "").strip()
    resume_text = data.get("resume", "").strip()

    if not all([company, role, resume_text]):
        return {"error": "Missing required fields: company, role, or resume"}, 400

    try:
        result = simulate_rejection(resume_text, company, role)
        return {"status": "success", "data": result}
    except Exception as e:
        print(f"Error in rejection simulator route: {e}")
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(debug=True)
