import sys
import os

# Add the project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')))

from models.ats_checker import check_ats_friendliness
from unittest.mock import patch, MagicMock

@patch('google.generativeai.GenerativeModel.generate_content')
def test_ats_checker_error_handling(mock_generate):
    # Simulate an API error
    mock_generate.side_effect = Exception("Simulated API Error")
    
    print("Testing error handling in check_ats_friendliness...")
    result = check_ats_friendliness("Fake resume text", "Fake JD")
    
    expected_keys = ["score", "role_focus", "missing_skills", "risk_analysis", "roadmap", "summary", "tips"]
    
    for key in expected_keys:
        if key not in result:
            print(f"FAILED: Missing key '{key}' in result")
            return
    
    if result["score"] == 0 and "Analysis failed" in result["missing_skills"]:
        print("SUCCESS: Error handling worked correctly and returned default values.")
    else:
        print("FAILED: Result did not match expected default values.")
        print(f"Result: {result}")

if __name__ == "__main__":
    test_ats_checker_error_handling()
