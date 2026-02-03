try:
    from groq import Groq
    print("Groq imported successfully")
except ImportError as e:
    print(f"Groq import failed: {e}")

try:
    from flask import Flask
    print("Flask imported successfully")
except ImportError as e:
    print(f"Flask import failed: {e}")

try:
    from models.resume_ranker import rank_resumes
    print("models.resume_ranker imported successfully")
except ImportError as e:
    print(f"models.resume_ranker import failed: {e}")

try:
    from models.ats_checker import check_ats_friendliness
    print("models.ats_checker imported successfully")
except ImportError as e:
    print(f"models.ats_checker import failed: {e}")

try:
    from models.job_expander import expand_job_requirements
    print("models.job_expander imported successfully")
except ImportError as e:
    print(f"models.job_expander import failed: {e}")

try:
    from models.file_parser import extract_text_from_file
    print("models.file_parser imported successfully")
except ImportError as e:
    print(f"models.file_parser import failed: {e}")

try:
    from models.style_analyzer import analyze_company_style
    print("models.style_analyzer imported successfully")
except ImportError as e:
    print(f"models.style_analyzer import failed: {e}")

try:
    from models.evolution_tracker import track_evolution
    print("models.evolution_tracker imported successfully")
except ImportError as e:
    print(f"models.evolution_tracker import failed: {e}")

try:
    from models.rejection_simulator import simulate_rejection
    print("models.rejection_simulator imported successfully")
except ImportError as e:
    print(f"models.rejection_simulator import failed: {e}")

print("Import check complete.")
