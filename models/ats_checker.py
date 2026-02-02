from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"

def check_ats_friendliness(resume_text, job_description=None):
    """
    Analyzes a resume for ATS friendliness, skill gaps, role-specific weighting, 
    and resume risks using Gemini AI.
    """
    
    role_weighting_context = ""
    if job_description:
        role_weighting_context = f"""
        Role-Specific Context:
        Analyze the Job Description provided below. Identify the core role.
        Apply weighted importance to skills based on the role.
        
        Job Description:
        {job_description}
        """

    prompt = f"""
    You are an expert ATS optimizer and high-stakes technical recruiter.
    Analyze the following resume text.
    
    {role_weighting_context}

    Provide a deep-dive analysis covering:
    1. **ATS Friendliness Score (0-100)**: Formatting, keywords, and structural clarity.
    2. **Role Focus**: Identify the primary job role.
    3. **Skill Match Analysis**: Identify matched skills and missing skills based on the JD.
    4. **Resume Risk Detector**: Identify elements that cause recruiter skepticism.
    5. **Resume Feedback Loop**: Actionable roadmap to reach the top 10%.
    
    CRITICAL: The "score" must be a weighted reflection of the "matched_skills" vs "missing_skills". 
    If a candidate has only 3 matched skills and 13 missing skills, the score should NOT be high (e.g., 75 is too high).
    
    Format your response as a valid JSON object with the following keys:
    "score": (int - carefully calculated),
    "role_focus": (string),
    "recommendation": (string - a professional 1-2 sentence recommendation for the hiring manager),
    "matched_skills": [
        {{"name": (string), "score": (int 0-100), "level": "Expert/Advanced/Intermediate/Beginner"}}
    ],
    "missing_skills": [(string), ...],
    "risk_analysis": {{
        "level": "High/Medium/Low",
        "findings": [(string), ...],
        "skepticism_reason": (string)
    }},
    "roadmap": [(string), (string), (string)],
    "summary": (string),
    "tips": [(string), ...],
    "feedback_loop": {{
        "current_percentile": (int),
        "gap_to_top_10": (int),
        "sections_to_improve": [
            {{
                "section": (string),
                "current_issue": (string),
                "improvement": (string),
                "impact": "High" | "Medium" | "Low"
            }}
        ],
        "quick_wins": [(string), ...],
        "major_upgrades": [(string), ...]
    }},
    "improvement_priority": [(string), ...]

    Resume Text:
    {resume_text}
    """
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        response_text = completion.choices[0].message.content
        from models.utils import extract_json
        result = extract_json(response_text)
        if result:
            return result
        raise ValueError("Failed to extract valid JSON from AI response")
    except Exception as e:
        print(f"Error checking advanced analysis: {e}")
        return {
            "score": 0,
            "role_focus": "Unknown",
            "missing_skills": ["Analysis failed"],
            "risk_analysis": {"level": "Unknown", "findings": ["Unable to analyze risks"], "skepticism_reason": "AI Error"},
            "roadmap": ["Review resume manually"],
            "summary": "AI error during analysis.",
            "recommendation": "Review resume manually due to analysis error.",
            "tips": ["Try again later."],
            "feedback_loop": {
                "current_percentile": 0,
                "gap_to_top_10": 100,
                "sections_to_improve": [],
                "quick_wins": ["Retry the analysis"],
                "major_upgrades": []
            },
            "improvement_priority": ["Retry analysis"]
        }
