from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()
def analyze_company_style(resume_text, target_company_type=None):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY not found in style_analyzer.")
        return {"error": "AI Service unavailable"}

    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Groq in style_analyzer: {e}")
        return {"error": "AI initialization failed"}

    MODEL_NAME = "llama-3.3-70b-versatile"
    """
    Analyzes resume writing style and matches against company culture preferences.
    
    Company cultures:
    - Microsoft: Structured, impact-driven, system thinking
    - Startup: Ownership, speed, breadth
    - Research: Depth, publications, rigor
    
    Checks:
    - Bullet length analysis
    - Quantification style (metrics, percentages)
    - Ownership language ("I led" vs "participated")
    - Engineering maturity signals
    """
    
    prompt = f"""
    You are a resume writing style expert who understands how different companies prefer resumes to be written.
    
    Analyze this resume's WRITING STYLE (not just content) and determine which company culture it best fits:
    
    Company Culture Preferences:
    1. **Microsoft/Big Tech**: Structured bullet points, impact-driven metrics, system-level thinking, 
       clear ownership statements, quantified achievements (%, $, scale numbers)
    2. **Startup**: Action-oriented, ownership language ("I built", "I drove"), breadth of skills,
       fast-paced project descriptions, entrepreneurial mindset signals
    3. **Research/Academic**: Deep technical depth, publication mentions, methodological rigor,
       longer detailed descriptions, theoretical background emphasis
    
    Analyze these specific elements:
    1. **Bullet Length**: Are bullets concise (startup-friendly) or detailed (research-friendly)?
    2. **Quantification Style**: Are achievements quantified with specific metrics?
    3. **Ownership Language**: Does the candidate use "I led", "I owned" vs passive "participated", "helped"?
    4. **Engineering Maturity**: Are there signals of senior-level thinking (architecture, scale, trade-offs)?
    
    Format your response as a valid JSON object:
    {{
        "best_fit_culture": "Microsoft" | "Startup" | "Research",
        "fit_score": (0-100 how well the style matches),
        "style_analysis": {{
            "bullet_length": {{
                "assessment": "Concise" | "Moderate" | "Detailed",
                "recommendation": (string with improvement tip)
            }},
            "quantification_style": {{
                "score": (0-100),
                "examples_found": [(string), ...],
                "recommendation": (string)
            }},
            "ownership_language": {{
                "score": (0-100),
                "strong_phrases": [(string), ...],
                "weak_phrases": [(string), ...],
                "recommendation": (string)
            }},
            "engineering_maturity": {{
                "level": "Junior" | "Mid" | "Senior" | "Staff+",
                "signals_found": [(string), ...],
                "recommendation": (string)
            }}
        }},
        "culture_match_breakdown": {{
            "microsoft_fit": (0-100),
            "startup_fit": (0-100),
            "research_fit": (0-100)
        }},
        "style_summary": (string - one-liner like "Your resume content fits Microsoft, but writing style matches startup culture more."),
        "top_style_improvements": [(string), (string), (string)]
    }}
    
    Resume Text:
    {resume_text}
    """
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a resume style expert that outputs JSON."},
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
        print(f"Error in style analysis: {e}")
        return {
            "best_fit_culture": "Unknown",
            "fit_score": 0,
            "style_analysis": {
                "bullet_length": {"assessment": "Unknown", "recommendation": "Unable to analyze"},
                "quantification_style": {"score": 0, "examples_found": [], "recommendation": "Unable to analyze"},
                "ownership_language": {"score": 0, "strong_phrases": [], "weak_phrases": [], "recommendation": "Unable to analyze"},
                "engineering_maturity": {"level": "Unknown", "signals_found": [], "recommendation": "Unable to analyze"}
            },
            "culture_match_breakdown": {"microsoft_fit": 0, "startup_fit": 0, "research_fit": 0},
            "style_summary": "Style analysis failed. Please try again.",
            "top_style_improvements": ["Retry analysis"]
        }
