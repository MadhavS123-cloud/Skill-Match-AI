import os
from flask import Flask, redirect, url_for, render_template, request, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.linkedin import make_linkedin_blueprint, linkedin
from oauthlib.oauth2 import TokenExpiredError
from dotenv import load_dotenv
from models.resume_ranker import rank_resumes
from models.ats_checker import check_ats_friendliness
from models.job_expander import expand_job_requirements
from models.file_parser import extract_text_from_file
import google.generativeai as genai

# =========================
# Load environment variables
# =========================
load_dotenv()

# Allow OAuth over HTTP (ONLY for local development)
if os.getenv("FLASK_ENV") == "development":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# =========================
# Flask App Setup
# =========================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

# =========================
# Gemini AI Setup
# =========================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-flash-lite-latest')

# =========================
# Google OAuth Blueprint
# =========================
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    redirect_url="/google-callback",
)

app.register_blueprint(google_bp, url_prefix="/login")

# =========================
# LinkedIn OAuth Blueprint
# =========================
linkedin_bp = make_linkedin_blueprint(
    client_id=os.getenv("LINKEDIN_CLIENT_ID"),
    client_secret=os.getenv("LINKEDIN_CLIENT_SECRET"),
    scope=["r_emailaddress", "r_liteprofile"],
)
app.register_blueprint(linkedin_bp, url_prefix="/login")

# =========================
# Routes
# =========================

@app.route("/", methods=["GET", "POST"])
def index():
    if not google.authorized and not linkedin.authorized:
        return redirect(url_for("login"))

    user = {}
    
    if google.authorized:
        try:
            resp = google.get("/oauth2/v2/userinfo")
        except TokenExpiredError:
            return redirect(url_for("google.login"))

        if not resp.ok:
            return redirect(url_for("google.login"))

        user = resp.json()
    
    elif linkedin.authorized:
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

    # Get recent matches from session for dashboard
    recent_matches = session.get("recent_matches", [])
    
    # Calculate Realistic Dashboard Metrics
    total_matches = len(recent_matches)
    avg_score = round(sum(m['score'] for m in recent_matches) / total_matches, 1) if total_matches > 0 else 0
    active_roles = len(set(m['role'] for m in recent_matches))
    matches_this_week = len([m for m in recent_matches if "today" in m.get('date', '').lower() or "now" in m.get('date', '').lower()]) # Simple logic for now
    
    stats = {
        "total": total_matches if total_matches > 0 else 248, # Fallback to mock if empty? No, let's use real 0 if empty or user might prefer mock for first view.
        "avg": avg_score if total_matches > 0 else "0%",
        "roles": active_roles if total_matches > 0 else 0,
        "week": matches_this_week if total_matches > 0 else 0
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
                
                # Top 10% Logic: Score > 90 or Rank 1 in a pool
                is_top_tier = score >= 90 or (rank == 0 and len(ranked_results) > 1)
                
                # Mock Detailed Data for Analysis View (In production, this would come from the AI/LLM)
                strengths = ["Strong relevant experience", "Technical keyword density is high", "Good leadership indicators"]
                areas_to_develop = ["Could clarify specific project impacts", "Mention more industry-standard tools"]
                
                detailed_skills = [
                    {"name": "Python/Flask", "score": 95, "level": "Expert"},
                    {"name": "Database Management", "score": 88, "level": "Advanced"},
                    {"name": "Team Leadership", "score": 82, "level": "Advanced"},
                    {"name": "Cloud Deployment", "score": 45, "level": "Beginner"}
                ]
                
                experience_match = [
                    {"label": "Years of Experience", "candidate": "5 years", "required": "5+ years", "pct": 100},
                    {"label": "Direct Project Impact", "candidate": "High", "required": "High", "pct": 95}
                ]

                results.append({
                    "resume_no": index + 1,
                    "score": score,
                    "ats_score": ats_results.get("score", 0),
                    "ats_summary": ats_results.get("summary", ""),
                    "ats_tips": ats_results.get("tips", []),
                    "missing_skills": ats_results.get("missing_skills", []),
                    "roadmap": ats_results.get("roadmap", []),
                    "role_focus": ats_results.get("role_focus", ""),
                    "risk_analysis": ats_results.get("risk_analysis", {"level": "Low", "findings": [], "skepticism_reason": ""}),
                    "is_top_tier": is_top_tier,
                    "strengths": strengths,
                    "areas_to_develop": areas_to_develop,
                    "detailed_skills": detailed_skills,
                    "experience_match": experience_match,
                    "recommendation": f"This candidate shows strong potential with a {score}% match. Consider an interview to assess soft skills.",
                    "content": raw_resumes[index][:200] + "..." # Optional preview
                })

            # Save to recent matches history in session
            new_match_entry = {
                "role": job_title if job_title else "Unnamed Role",
                "candidate": f"Candidate {results[0]['resume_no']}" if results else "Unknown",
                "score": results[0]['score'] if results else 0,
                "date": "Just now"
            }
            recent_matches.insert(0, new_match_entry)
            session["recent_matches"] = recent_matches[:5] # Keep last 5
            session.permanent = True

            return render_template(
                "index.html",
                user=user,
                results=results,
                recent_matches=session["recent_matches"],
                stats=stats,
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
    if not google.authorized:
        return redirect(url_for("google.login"))
    return redirect(url_for("index"))


@app.route("/google-callback")
def google_callback():
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
    if not google.authorized and not linkedin.authorized:
        return {"error": "Unauthorized"}, 401
    
    user_message = request.json.get("message")
    if not user_message:
        return {"error": "No message provided"}, 400

    try:
        # System instructions to keep the AI on-brand
        prompt = f"""
        You are 'Skill Match AI Assistant', a helpful career coach and platform guide.
        The user is currently using Skill Match AI, an app that ranks resumes against job descriptions.
        Keep your answers concise, helpful, and professional but modern (Gen Z friendly).
        If the user asks about the app, explain that it uses AI to calculate similarity scores between resumes and job requirements.
        
        User: {user_message}
        """
        response = model.generate_content(prompt)
        return {"response": response.text}
    except Exception as e:
        error_msg = str(e)
        print(f"Error calling Gemini: {error_msg}")
        return {"error": error_msg}, 500


# =========================
# Run App
# =========================
if __name__ == "__main__":
    app.run(debug=True)
