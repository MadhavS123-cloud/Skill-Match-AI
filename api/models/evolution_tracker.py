import json

def track_evolution(old_analysis, new_analysis):
    """
    Compares two resume analyses to track progression.
    Returns delta score, progression signals, and key improvements.
    """
    if not old_analysis:
        return None

    old_score = old_analysis.get('score', 0)
    new_score = new_analysis.get('score', 0)
    delta = new_score - old_score

    signals = []
    
    # Check for skill progression
    old_missing = set(old_analysis.get('missing_skills', []))
    new_missing = set(new_analysis.get('missing_skills', []))
    
    filled_gaps = old_missing - new_missing
    if filled_gaps:
        signals.append({
            "type": "skill_filled",
            "message": f"Successfully added key skills: {', '.join(list(filled_gaps)[:3])}",
            "impact": "High"
        })

    # Check for risk reduction
    old_risks = old_analysis.get('risk_analysis', {}).get('level', 'Low')
    new_risks = new_analysis.get('risk_analysis', {}).get('level', 'Low')
    
    risk_improved = (old_risks == 'High' and new_risks in ['Medium', 'Low']) or (old_risks == 'Medium' and new_risks == 'Low')
    if risk_improved:
        signals.append({
            "type": "risk_reduced",
            "message": f"Resume skepticism reduced from {old_risks} to {new_risks}",
            "impact": "Medium"
        })

    # Check for formatting/ATS improvement
    old_ats = old_analysis.get('ats_score', 0)
    new_ats = new_analysis.get('ats_score', 0)
    if new_ats > old_ats:
        signals.append({
            "type": "ats_improved",
            "message": f"ATS optimization improved by {new_ats - old_ats}%",
            "impact": "Low"
        })

    # Top takeaway
    takeaway = "Your resume is evolving! "
    if delta > 0:
        takeaway += f"Score increased by +{delta} points due to better skill alignment."
    elif delta < 0:
        takeaway += "Score slightly decreased. Ensure the new changes didn't remove critical keywords."
    else:
        takeaway += "No major score change, but structural elements may have improved."

    return {
        "delta": delta,
        "old_score": old_score,
        "new_score": new_score,
        "signals": signals,
        "takeaway": takeaway
    }
