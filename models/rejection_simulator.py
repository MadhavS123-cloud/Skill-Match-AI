from groq import Groq
import os
import json

def simulate_rejection(resume_text, company, role):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key: return {"error": "Missing key"}
    try:
        client = Groq(api_key=api_key)
        prompt = f"Simulate a cynical HR manager rejecting this resume for {role} at {company}. Output JSON with rejection_risks, internal_monologue, line_of_doubt, strategic_fixes. Resume: {resume_text}"
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception:
        return {"error": "Simulator failed"}
