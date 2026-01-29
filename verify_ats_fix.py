from models.ats_checker import check_ats_friendliness
import os
from dotenv import load_dotenv

load_dotenv()

def test_analysis():
    print("Testing advanced analysis with gemini-flash-lite-latest...")
    
    resume_text = """
    John Doe
    Software Engineer with 5 years of experience in Python, Flask, and AWS.
    Built multiple scalable microservices.
    """
    
    jd = "Software Engineer with experience in Python and cloud deployment."
    
    result = check_ats_friendliness(resume_text, jd)
    
    print("\nResult Analysis:")
    print(f"Score: {result.get('score')}")
    print(f"Role Focus: {result.get('role_focus')}")
    print(f"Missing Skills: {result.get('missing_skills')}")
    print(f"Summary: {result.get('summary')}")
    
    if result.get('summary') == "AI error during analysis.":
        print("\nFAILURE: AI error still present.")
    else:
        print("\nSUCCESS: Analysis completed successfully.")

if __name__ == "__main__":
    test_analysis()
