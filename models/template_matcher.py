def get_company_templates():
    return {
        "Google": {
            "name": "Data-Driven Engineer",
            "description": "Focuses on scale, metrics, and quantitative achievements.",
            "style": "Structured, result-oriented",
            "structure": "Name -> Contact -> Summary -> Experience (Scale focused) -> Projects -> Education"
        },
        "Amazon": {
            "name": "Customer Obsessed Leader",
            "description": "Emphasis on Ownership, Delivering Results, and Leadership Principles.",
            "style": "Action-oriented, multi-dimensional",
            "structure": "Name -> Contact -> Summary (Ownership) -> Experience (LP oriented) -> Leadership Impact -> Skills"
        },
        "Startups": {
            "name": "High-Velocity Builder",
            "description": "Highlights rapid shipping, breadth of skills, and zero-to-one ownership.",
            "style": "Fast-paced, versatile",
            "structure": "Name -> Contact -> Key Accomplishments -> Technical Stack -> Rapid Growth Experience"
        }
    }

def suggest_template(style_analysis):
    fit = style_analysis.get("best_fit_culture", "Startup").lower()
    templates = get_company_templates()
    if "microsoft" in fit or "tech" in fit: return templates["Google"]
    if "amazon" in fit: return templates["Amazon"]
    return templates["Startups"]
