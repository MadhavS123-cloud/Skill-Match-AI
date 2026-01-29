import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-flash-lite-latest')

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
    3. **Skill Gap Intelligence**: Comparison against JD. List exactly what is missing.
    4. **Resume Risk Detector**: Identify elements that cause recruiter skepticism:
        - Buzzword Stuffing (listing too many technical terms without context)
        - Fake-looking Experience (template-driven or unrealistic descriptions)
        - Unrealistic Timelines (implausible growth or overlapping dates)
        - Suspicious Skill Density (advanced skills without corresponding work evidence)
    5. **Resume Feedback Loop**: Actionable roadmap to reach the top 10%.
    6. **Summary**: Brief overview of the resume's strength.

    Format your response as a valid JSON object with the following keys:
    "score": (int),
    "role_focus": (string),
    "missing_skills": [(string), (string), ...],
    "risk_analysis": {{
        "level": "High/Medium/Low",
        "findings": [(string), (string), ...],
        "skepticism_reason": (string)
    }},
    "roadmap": [(string), (string), (string)],
    "summary": (string),
    "tips": [(string), (string), ...]

    Resume Text:
    {resume_text}
    """
    
    try:
        response = model.generate_content(prompt)
        text_response = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(text_response)
        return result
    except Exception as e:
        print(f"Error checking advanced analysis: {e}")
        return {
            "score": 0,
            "role_focus": "Unknown",
            "missing_skills": ["Analysis failed"],
            "risk_analysis": {"level": "Unknown", "findings": ["Unable to analyze risks"], "skepticism_reason": "AI Error"},
            "roadmap": ["Review resume manually"],
            "summary": "AI error during analysis.",
            "tips": ["Try again later."]
        }
