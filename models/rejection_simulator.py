from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"

def simulate_rejection(resume_text, company, role):
    """
    Simulates a hiring manager's rejection process for a specific company and role.
    """
    
    prompt = f"""
    You are a cynical, high-stakes Hiring Manager at {company} looking for a {role}.
    You are reviewing the following resume and looking for reasons to REJECT it. 
    Be brutally honest but professional, simulating internal corporate skepticism.

    Analyze the resume for {company}'s specific culture and the {role}'s requirements.

    Provide the following in your analysis:
    1. **Top 5 Rejection Risks**: Specific reasons why this candidate might be a "no".
    2. **Internal Monologue**: A 1-2 sentence "internal voice" comment on the candidate (e.g., "Good on paper, but hasn't shipped anything at scale").
    3. **The 'Line of Doubt'**: The exact line or detail from the resume that triggered the most skepticism.
    4. **Decision-Based Fixes**: What should the candidate CHANGE in their experience or presentation to reduce these risks? (Not just adding keywords, but strategic shifts).

    Format your response as a valid JSON object with the following keys:
    "rejection_risks": [(string), (string), (string), (string), (string)],
    "internal_monologue": (string),
    "line_of_doubt": (string),
    "strategic_fixes": [(string), (string), (string)]

    Resume Text:
    {resume_text}
    """
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a cynical hiring manager that outputs JSON."},
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
        print(f"Error simulating rejection: {e}")
        return {
            "rejection_risks": ["Analysis failed due to an error.", "Please check your input or try again later."],
            "internal_monologue": "The system encountered an error while trying to think like a hiring manager.",
            "line_of_doubt": "N/A",
            "strategic_fixes": ["Verify the application logs if you are an administrator."]
        }
