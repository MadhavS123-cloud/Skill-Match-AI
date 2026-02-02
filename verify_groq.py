import os
import sys
from dotenv import load_dotenv

# Ensure we can import from models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.ats_checker import check_ats_friendliness
from models.rejection_simulator import simulate_rejection
from models.job_expander import expand_job_requirements
from models.style_analyzer import analyze_company_style

load_dotenv()

def test_groq_integration():
    resume_text = "John Doe, Software Engineer with experience in Python, Flask, and Groq API."
    jd = "Software Engineer specialized in Python and AI integrations."
    company = "TechCorp"
    role = "Senior Python Developer"

    print("--- Testing ATS Checker ---")
    try:
        ats_result = check_ats_friendliness(resume_text, jd)
        print(f"ATS Score: {ats_result.get('score')}")
        print(f"Summary: {ats_result.get('summary')[:50]}...")
    except Exception as e:
        print(f"ATS Checker Failed: {e}")

    print("\n--- Testing Rejection Simulator ---")
    try:
        rejection_result = simulate_rejection(resume_text, company, role)
        print(f"Risks: {rejection_result.get('rejection_risks')[0]}")
    except Exception as e:
        print(f"Rejection Simulator Failed: {e}")

    print("\n--- Testing Job Expander ---")
    try:
        expanded_jd, changed = expand_job_requirements("Python Developer")
        print(f"Expanded JD Length: {len(expanded_jd)}")
    except Exception as e:
        print(f"Job Expander Failed: {e}")

    print("\n--- Testing Style Analyzer ---")
    try:
        style_result = analyze_company_style(resume_text)
        print(f"Best Fit: {style_result.get('best_fit_culture')}")
    except Exception as e:
        print(f"Style Analyzer Failed: {e}")

if __name__ == "__main__":
    test_groq_integration()
