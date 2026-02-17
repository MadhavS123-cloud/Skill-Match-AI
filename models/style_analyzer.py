import re

def analyze_company_style(resume_text):
    """
    Analyzes resume style against corporate cultures using local heuristics.
    """
    text = resume_text.lower()
    
    # Heuristics for different cultures
    research_keywords = ["published", "research", "phd", "algorithm", "theoretical", "publication", "conference"]
    startup_keywords = ["built", "scaled", "growth", "mvp", "from scratch", "unstructured", "speed", "traction"]
    big_tech_keywords = ["distributed systems", "large scale", "optimized", "collaborated", "stakeholder", "architecture", "standardized"]
    
    research_count = sum(1 for k in research_keywords if k in text)
    startup_count = sum(1 for k in startup_keywords if k in text)
    big_tech_count = sum(1 for k in big_tech_keywords if k in text)
    
    scores = {
        "Research": research_count,
        "Startup": startup_count,
        "Big Tech": big_tech_count
    }
    
    best_fit = max(scores, key=scores.get)
    max_score = scores[best_fit]
    
    # Normalize score 0-100 (naive scaling)
    fit_score = min(90, 40 + (max_score * 10))
    
    summaries = {
        "Research": "Focuses heavily on theoretical depth and formal contributions.",
        "Startup": "Emphasizes speed, versatility, and building from zero.",
        "Big Tech": "Highlights experience with scale, process, and complex systems."
    }
    
    return {
        "best_fit_culture": best_fit,
        "fit_score": fit_score,
        "style_summary": summaries[best_fit],
        "top_style_improvements": [
            "Add more data-driven metrics" if best_fit != "Research" else "Include more peer-reviewed citations",
            "Showcase more end-to-end ownership",
            "Standardize formatting for ATS readability"
        ]
    }
