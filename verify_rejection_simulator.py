import sys
import os

# Add the project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.rejection_simulator import simulate_rejection

def test_simulator():
    resume = """
    John Doe
    Full Stack Developer
    
    Experience:
    - Built a todo app using Python and Flask.
    - Used HTML/CSS for the frontend.
    - 6 months experience at a local startup.
    
    Skills: Python, JavaScript, HTML, CSS.
    """
    
    company = "Google"
    role = "Senior Staff Software Engineer"
    
    print(f"Simulating rejection for {role} at {company}...")
    result = simulate_rejection(resume, company, role)
    
    print("\n--- Simulation Results ---")
    print(f"Internal Monologue: {result.get('internal_monologue')}")
    print(f"Line of Doubt: {result.get('line_of_doubt')}")
    print("\nRejection Risks:")
    for risk in result.get('rejection_risks', []):
        print(f"- {risk}")
    
    print("\nStrategic Fixes:")
    for fix in result.get('strategic_fixes', []):
        print(f"- {fix}")

if __name__ == "__main__":
    test_simulator()
