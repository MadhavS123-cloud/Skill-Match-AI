from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()
def expand_job_requirements(input_text):
    """
    Expands a short job title or brief description into a full, industry-standard JD.
    If the input is already a full JD, it returns it as is.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY not found in job_expander.")
        return input_text, False

    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Groq in job_expander: {e}")
        return input_text, False

    MODEL_NAME = "llama-3.3-70b-versatile"
    # Heuristic: If it's more than 300 characters, consider it a full JD already
    if len(input_text.strip()) > 300:
        return input_text, False

    prompt = f"""
    You are an expert technical recruiter and HR specialist.
    The user has provided a short job title or brief role description: "{input_text}"
    
    Expand this into a comprehensive, professional, and realistic Job Description.
    Include:
    1. Role Overview
    2. Core Responsibilities (Bullet points)
    3. Required Technical Skills (Bullet points)
    4. Required Soft Skills/Qualifications (Bullet points)
    5. Company-specific context (if a company like 'Google', 'Amazon', etc., is mentioned).

    Return ONLY the expanded text content. Do not include any JSON or metadata.
    """

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert technical recruiter."},
                {"role": "user", "content": prompt},
            ],
        )
        expanded_text = completion.choices[0].message.content.strip()
        return expanded_text, True
    except Exception as e:
        print(f"Error expanding job requirements: {e}")
        return input_text, False
