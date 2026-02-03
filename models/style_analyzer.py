from groq import Groq
import os
import json

def analyze_company_style(resume_text):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key: return {"error": "Missing key"}
    try:
        client = Groq(api_key=api_key)
        prompt = f"Analyze resume style for fit in Big Tech, Startup, or Research. Output JSON with best_fit_culture, fit_score, style_summary, top_style_improvements. Resume: {resume_text}"
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception:
        return {"error": "Style analysis failed"}
