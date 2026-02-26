import os
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ================================================
# Gemini AI Setup (primary engine when key exists)
# ================================================
try:
    import google.generativeai as genai
    _GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    if _GEMINI_KEY:
        genai.configure(api_key=_GEMINI_KEY)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        GEMINI_AVAILABLE = True
    else:
        _gemini_model = None
        GEMINI_AVAILABLE = False
except ImportError:
    genai = None
    _gemini_model = None
    GEMINI_AVAILABLE = False

# ================================================
# Ollama (local LLM fallback)
# ================================================
try:
    import ollama
except ImportError:
    ollama = None


def call_gemini(prompt, system_prompt="You are a helpful career assistant."):
    """
    Calls the Google Gemini API for rich AI analysis.
    Returns None on failure so callers can fall back to local logic.
    """
    if not GEMINI_AVAILABLE or _gemini_model is None:
        return None
    try:
        full_prompt = f"{system_prompt}\n\n{prompt}"
        response = _gemini_model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


def call_local_llm(prompt, system_prompt="You are a helpful career assistant."):
    """
    AI call hierarchy:
      1. Google Gemini (if API key is set) — rich, cloud AI
      2. Ollama (if installed locally) — local LLM
      3. Deterministic fallback — rule-based response
    """
    # Try Gemini first
    gemini_response = call_gemini(prompt, system_prompt)
    if gemini_response:
        return gemini_response

    # Try Ollama next
    if ollama:
        try:
            response = ollama.chat(model='llama3', messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ])
            return response['message']['content']
        except Exception:
            pass

    return "AI analysis service is not available. Using deterministic fallback logic."


def calculate_similarity(text1, text2):
    """
    Calculates similarity using lightweight TF-IDF (Credit-free & Hosting-friendly).
    """
    try:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        return float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
    except Exception:
        return 0.0


def extract_skills_locally(text):
    """
    Extracts common tech skills using regex (fast/deterministic).
    """
    common_skills = [
        "Python", "JavaScript", "Java", "C++", "C#", "React", "Angular", "Vue", "Node.js",
        "AWS", "Azure", "GCP", "Kubernetes", "Docker", "SQL", "NoSQL", "MongoDB", "PostgreSQL",
        "Machine Learning", "AI", "Cloud Computing", "DevOps", "Microservices", "REST API",
        "GraphQL", "TypeScript", "Go", "Rust", "Swift", "Kotlin", "TensorFlow", "PyTorch",
        "Pandas", "Scikit-learn", "Hadoop", "Spark", "Tableau", "PowerBI", "Agile", "Scrum"
    ]
    found = []
    text_upper = text.upper()
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill.upper()) + r'\b', text_upper):
            found.append(skill)
    return found


def match_skills_semantic(resume_text, required_skills):
    """
    Checks for required skills in resume using lightweight matching.
    """
    if not required_skills:
        return [], []

    found = []
    missing = []
    resume_lower = resume_text.lower()

    for skill in required_skills:
        if skill.lower() in resume_lower:
            found.append(skill)
        else:
            missing.append(skill)

    return found, missing
