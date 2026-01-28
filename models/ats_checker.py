import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-flash-latest')

def check_ats_friendliness(resume_text):
    """
    Analyzes a resume for ATS friendliness using Gemini AI.
    Returns a dictionary containing score and feedback.
    """
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) optimizer. 
    Analyze the following resume text and provide:
    1. An ATS Friendliness Score (0-100).
    2. A list of 3-5 specific, actionable improvement tips.
    3. A brief summary of why it received this score.

    Format your response as a valid JSON object with the following keys:
    "score": (int),
    "summary": (string),
    "tips": [(string), (string), ...]

    Resume Text:
    {resume_text}
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean the response to ensure it's valid JSON
        text_response = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(text_response)
        return result
    except Exception as e:
        print(f"Error checking ATS friendliness: {e}")
        return {
            "score": 0,
            "summary": "AI was unable to analyze this resume at the moment.",
            "tips": ["Ensure your resume is in plain text format.", "Try again later."]
        }
