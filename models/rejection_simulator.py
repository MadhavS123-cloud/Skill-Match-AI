from .local_ai import call_local_llm, calculate_similarity, extract_skills_locally
import json

def simulate_rejection(resume_text, company, role):
    """
    Simulates a rejection using local AI (Ollama) or deterministic logic if offline.
    """
    
    # 1. Try Ollama for rich, cynical personality
    prompt = f"""
    Simulate a cynical, high-stakes HR manager at {company} rejecting this resume for a {role} position.
    Be brutal but constructive.
    Output MUST be a JSON object with:
    - rejection_risks: list of 3 specific red flags
    - internal_monologue: a short, blunt string of what they actually think
    - line_of_doubt: a specific 1-line quote from the resume that made them stop
    - strategic_fixes: list of 3 high-impact changes to get past them next time

    IMPORTANT: Do NOT use ANY emojis in your response. Keep the tone cynical but professional.

    Resume Content:
    {resume_text[:2000]}  # Truncate for local LLM context limits
    """
    
    system_prompt = "You are a cynical hiring manager who provides feedback in JSON format."
    
    response = call_local_llm(prompt, system_prompt)
    
    try:
        # If response looks like JSON, parse it
        if '{' in response and '}' in response:
            json_str = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_str)
    except:
        pass

    # 2. Deterministic Fallback (if Ollama is not running)
    similarity = calculate_similarity(resume_text, f"{role} at {company}")
    resume_skills = extract_skills_locally(resume_text)
    
    monologue = "This resume feels generic. I've seen 50 of these today."
    if similarity < 0.4:
        monologue = "Is this candidate even applying for the right job? The alignment is way off."
    elif len(resume_skills) < 5:
        monologue = "Too light on specific technical keywords. Probably won't survive the first round of interviews."

    return {
        "rejection_risks": [
            "Lack of specific industry-standard keywords" if len(resume_skills) < 10 else "Experience level appears slightly below bracket",
            "Formatting is basic and doesn't stand out in a high-volume pile",
            "Missing clear impact metrics in recent roles"
        ],
        "internal_monologue": monologue,
        "line_of_doubt": "The presentation lacks the 'wow' factor required for a top-tier firm like " + company,
        "strategic_fixes": [
            "Inject specific metrics (%, $) into every single experience bullet point",
            "Re-align the summary to speak directly to " + company + "'s core business values",
            "Modernize the layout to be more visually striking while maintaining ATS readability"
        ]
    }
