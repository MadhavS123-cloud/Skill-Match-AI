def track_evolution(old_analysis, new_analysis):
    if not old_analysis: return None
    old_score = old_analysis.get('score', 0)
    new_score = new_analysis.get('score', 0)
    delta = new_score - old_score
    signals = []
    if delta > 0:
        signals.append({"type": "improvement", "message": f"Score improved by {delta} points!", "impact": "High"})
    return {"delta": delta, "old_score": old_score, "new_score": new_score, "signals": signals, "takeaway": "Progression tracked."}
