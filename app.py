import os
from flask import Flask, redirect, url_for, render_template, request, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.linkedin import make_linkedin_blueprint, linkedin
from oauthlib.oauth2 import TokenExpiredError
from dotenv import load_dotenv
from models.resume_ranker import rank_resumes
from models.ats_checker import check_ats_friendliness
import google.generativeai as genai

# =========================
# Load environment variables
# =========================
load_dotenv()

# Allow OAuth over HTTP (ONLY for local development)
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
model = genai.GenerativeModel('gemini-flash-latest')

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

    results = None

    if request.method == "POST":
        job_description = request.form["job_description"]
        # Split resumes by double newline and filter empty ones
        raw_resumes = [r.strip() for r in request.form["resumes"].split("\n\n") if r.strip()]

        if raw_resumes:
            ranked_results = rank_resumes(raw_resumes, job_description)
            
            results = []
            for rank, (index, score_vec) in enumerate(ranked_results):
                score = round(float(score_vec[0]) * 100, 1)
                ats_results = check_ats_friendliness(raw_resumes[index])
                results.append({
                    "resume_no": index + 1,
                    "score": score,
                    "ats_score": ats_results.get("score", 0),
                    "ats_summary": ats_results.get("summary", ""),
                    "ats_tips": ats_results.get("tips", []),
                    "content": raw_resumes[index][:200] + "..." # Optional preview
                })

    return render_template(
        "index.html",
        user=user,
        results=results
    )



@app.route("/login")
def login():
    return render_template("login.html")


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
