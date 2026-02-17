import json

# Deterministic Salary Data
SALARY_BASE_DATA = {
    "software engineer": 80000,
    "backend engineer": 85000,
    "frontend engineer": 82000,
    "fullstack engineer": 88000,
    "data scientist": 95000,
    "product manager": 90000,
    "devops engineer": 92000,
    "qa engineer": 65000,
    "ui/ux designer": 75000,
    "mobile developer": 85000,
    "security engineer": 100000,
    "manager": 110000,
    "director": 150000,
    "default": 70000
}

LOCATION_MULTIPLIERS = {
    "us": 1.0,
    "usa": 1.0,
    "united states": 1.0,
    "san francisco": 1.4,
    "new york": 1.3,
    "london": 0.9,
    "uk": 0.85,
    "india": 0.25,
    "germany": 0.85,
    "canada": 0.9,
    "remote": 0.95,
    "singapore": 1.1
}

COMPANY_TIER_MULTIPLIERS = {
    "big tech": 1.5,
    "faang": 1.6,
    "mid-sized": 1.0,
    "startup": 0.9,
    "service": 0.7,
    "default": 1.0
}

EDUCATION_MULTIPLIERS = {
    "phd": 1.25,
    "masters": 1.1,
    "bachelors": 1.0,
    "self-taught": 0.95,
    "default": 1.0
}

SENIORITY_MULTIPLIERS = {
    "beginner": 0.8,
    "intermediate": 1.0,
    "advanced": 1.3,
    "expert": 1.5,
    "default": 1.0
}

def estimate_salary(role, company, location, experience, resume_score, education="", seniority=""):
    """
    Simulates a salary range using deterministic logic (Credit-free).
    """
    # 1. Clean inputs
    role_lower = role.lower()
    loc_lower = location.lower()
    comp_lower = company.lower()
    edu_lower = education.lower() if education else "default"
    sen_lower = seniority.lower() if seniority else "default"
    
    # 2. Base salary
    base = SALARY_BASE_DATA.get("default")
    for key, val in SALARY_BASE_DATA.items():
        if key in role_lower:
            base = val
            break
            
    # 3. Location multiplier
    loc_mult = LOCATION_MULTIPLIERS.get("us")
    for key, val in LOCATION_MULTIPLIERS.items():
        if key in loc_lower:
            loc_mult = val
            break
            
    # 4. Company Tier
    tier = "Mid-sized"
    tier_mult = COMPANY_TIER_MULTIPLIERS["default"]
    
    big_tech_keywords = ["google", "meta", "apple", "amazon", "microsoft", "netflix", "uber", "airbnb", "stripe"]
    if any(k in comp_lower for k in big_tech_keywords):
        tier = "Big Tech"
        tier_mult = COMPANY_TIER_MULTIPLIERS["big tech"]
    elif "startup" in comp_lower or "seed" in comp_lower:
        tier = "Startup"
        tier_mult = COMPANY_TIER_MULTIPLIERS["startup"]
    elif "service" in comp_lower or "consulting" in comp_lower or "tcs" in comp_lower or "infosys" in comp_lower:
        tier = "Service"
        tier_mult = COMPANY_TIER_MULTIPLIERS["service"]
        
    # 5. Experience multiplier
    # Rule: ~5-7% increase per year, slowing down after 10 years
    experience = float(experience)
    if experience <= 10:
        exp_mult = 1 + (experience * 0.08)
    else:
        exp_mult = 1.8 + ((experience - 10) * 0.03)
        
    # 6. Education multiplier
    edu_mult = EDUCATION_MULTIPLIERS.get(edu_lower, EDUCATION_MULTIPLIERS["default"])
    if "phd" in edu_lower: edu_mult = EDUCATION_MULTIPLIERS["phd"]
    elif "masters" in edu_lower: edu_mult = EDUCATION_MULTIPLIERS["masters"]
    
    # 7. Seniority multiplier
    sen_mult = SENIORITY_MULTIPLIERS.get(sen_lower, SENIORITY_MULTIPLIERS["default"])
    
    # Final Calculation
    calculated_avg = base * loc_mult * tier_mult * exp_mult * edu_mult * sen_mult
    
    # Range based on resume score (quality adjustment)
    # Score 50 is neutral. 100 adds 15%. 0 removes 15%.
    score_adj = 1 + ((float(resume_score) - 50) / 100 * 0.3)
    final_avg = calculated_avg * score_adj
    
    # Set currency symbol
    currency = "$"
    if "india" in loc_lower:
        currency = "₹"
    elif "uk" in loc_lower or "london" in loc_lower:
        currency = "£"
    elif "europe" in loc_lower or "germany" in loc_lower or "france" in loc_lower:
        currency = "€"

    def format_val(v):
        if currency == "₹":
            # For INR, use Lakhs if large
            if v >= 100000:
                return f"{currency}{v/100000:.1f}L"
            return f"{currency}{int(v):,}"
        if v >= 1000:
            return f"{currency}{int(v/1000)}k"
        return f"{currency}{int(v):,}"

    min_val = final_avg * 0.85
    max_val = final_avg * 1.25
    
    bonus_stock = "N/A"
    if tier == "Big Tech":
        bonus_stock = "15-25% Annual Bonus + RSU Package"
    elif tier == "Startup":
        bonus_stock = "0.05% - 0.2% Equity + Performance Bonus"
    elif final_avg > 100000:
        bonus_stock = "10% Performance Bonus"

    explanation = f"Based on {role} market rates in {location}. Adjusted for {experience} years of experience, {tier} compensation structure, and a resume strength of {resume_score}%."

    return {
        "company_tier": tier,
        "salary_range": {
            "min": format_val(min_val),
            "avg": format_val(final_avg),
            "max": format_val(max_val)
        },
        "bonus_stock": bonus_stock,
        "explanation": explanation,
        "confidence": "High (Deterministic)"
    }
