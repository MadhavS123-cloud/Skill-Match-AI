from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()

def simulate_rejection(resume_text, company, role):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key: 
        return {
            "rejection_risks": ["Service unavailable (Missing API Key)"],
            "internal_monologue": "I can't even look at this right now. The system is down.",
            "line_of_doubt": "Configuration Error",
            "strategic_fixes": ["Contact support to fix API connectivity."]
        }
    
    try:
        client = Groq(api_key=api_key)
        prompt = f"""
        Simulate a cynical, high-stakes HR manager at {company} rejecting this resume for a {role} position.
        Be brutal but constructive.
        Output MUST be a JSON object with:
        - rejection_risks: list of 3 specific red flags
        - internal_monologue: a short, blunt string of what they actually think
        - line_of_doubt: a specific 1-line quote from the resume that made them stop
        - strategic_fixes: list of 3 high-impact changes to get past them next time

        Resume Content:
        {resume_text}
        """
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Simulator Error: {e}")
        return {
            "rejection_risks": ["AI Simulator Failed"],
            "internal_monologue": "My brain just melted trying to process this. Error in simulation logic.",
            "line_of_doubt": "System Interrupt",
            "strategic_fixes": ["Try again in a few minutes.", "Check if Groq API is reachable."]
        }
