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
        "Meta": {
            "name": "Product-Focused Builder",
            "description": "Focuses on shipping fast, product impact, and user-centric features.",
            "style": "Fast-paced, product-driven",
            "structure": "Name -> Contact -> Experience (Impact focused) -> Product Projects -> Technical Skills"
        },
        "Microsoft": {
            "name": "Inclusive System Architect",
            "description": "Emphasis on collaboration, long-term stability, and technical depth.",
            "style": "Professional, depth-oriented",
            "structure": "Name -> Contact -> Profile -> Professional Experience -> Technical Leadership -> Education"
        },
        "Apple": {
            "name": "Design-First Engineer",
            "description": "Focuses on precision, aesthetics, and user experience.",
            "style": "Minimalist, detail-oriented",
            "structure": "Name -> Contact -> Technical Proficiencies -> Experience (Detail focused) -> Portfolio link"
        },
        "Netflix": {
            "name": "Context-Driven High Performer",
            "description": "Focuses on radical transparency, context over control, and stunning colleagues.",
            "style": "Direct, performance-heavy",
            "structure": "Name -> Contact -> Summary of Impact -> Experience (Decision making focus) -> Skills"
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
    if "google" in fit: return templates["Google"]
    if "amazon" in fit: return templates["Amazon"]
    if "meta" in fit or "facebook" in fit: return templates["Meta"]
    if "microsoft" in fit: return templates["Microsoft"]
    if "apple" in fit: return templates["Apple"]
    if "netflix" in fit: return templates["Netflix"]
    return templates["Startups"]
