from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()
def check_ats_friendliness(resume_text, job_description=None):
    """
    Analyzes a resume for ATS friendliness, skill gaps, role-specific weighting, 
    and resume risks using Groq AI.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"score": 0, "summary": "Missing API Key"}
    
    try:
        client = Groq(api_key=api_key)
    except Exception:
        return {"score": 0, "summary": "AI initialization failed."}

    MODEL_NAME = "llama-3.3-70b-versatile"
    
    role_weighting_context = ""
    if job_description:
        role_weighting_context = f"Job Description:\n{job_description}"

    prompt = f"""
    Analyze this resume for ATS friendliness.
    {role_weighting_context}
    
    Format response as JSON:
    "score": (0-100),
    "role_focus": (string),
    "matched_skills": [{{ "name": (str), "level": (str) }}],
    "missing_skills": [(str)],
    "risk_analysis": {{ "level": (str), "findings": [(str)] }},
    "roadmap": [(str)],
    "summary": (str),
    "tips": [(str)],
    "feedback_loop": {{ "current_percentile": (int), "gap_to_top_10": (int), "sections_to_improve": [] }}
    
    Resume:
    {resume_text}
    """
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": "You are an ATS expert that outputs JSON."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        # Using a simplified parse for now
        return json.loads(completion.choices[0].message.content)
    except Exception:
        return {"score": 0, "summary": "Analysis failed."}
