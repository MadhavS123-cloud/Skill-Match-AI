import os
import json
from groq import Groq

def estimate_salary(role, company, location, experience, resume_score, education="", seniority=""):
    """
    Simulates a salary range using Groq AI.
    """
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    prompt = f"""
    Estimate a realistic annual salary range for the following candidate profile:
    - Role: {role}
    - Company: {company}
    - Location: {location}
    - Years of Experience: {experience}
    - Resume Strength Score: {resume_score}/100
    - Education: {education}
    - Seniority Level: {seniority}

    Requirements:
    1. Categorize the company tier (Big Tech, Mid-sized, Startup, or Service).
    2. Provide a realistic salary range (Min, Average, Max).
    3. Factors to consider:
       - Location-based cost of living and market rates.
       - Experience multiplier.
       - Resume strength (Higher score = higher end of the range).
       - Company tier pay scales.
    4. Include an estimated Bonus/Stock indicator if applicable.
    5. Provide a short, data-driven explanation for the range.
    6. Assign a confidence indicator (Low, Medium, High).
    7. NO emojis in the response.

    Return the result ONLY as a JSON object with this structure:
    {{
        "company_tier": "string",
        "salary_range": {{
            "min": "string with currency symbol",
            "avg": "string with currency symbol",
            "max": "string with currency symbol"
        }},
        "bonus_stock": "string",
        "explanation": "string",
        "confidence": "Low/Medium/High"
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional compensation analyst specialized in tech salaries. Provide data-driven, realistic salary estimates without using emojis."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"Salary estimation failed: {e}")
        # Fallback logic if AI fails
        base = 50000
        if "india" in location.lower():
            base = 1000000
            symbol = "INR"
        else:
            symbol = "$"
            
        return {
            "company_tier": "Unknown",
            "salary_range": {
                "min": f"{symbol}{base}",
                "avg": f"{symbol}{base * 1.5}",
                "max": f"{symbol}{base * 2}"
            },
            "bonus_stock": "N/A",
            "explanation": "Calculation based on general market averages due to AI unavailability.",
            "confidence": "Low"
        }
