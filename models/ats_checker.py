from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()
def check_ats_friendliness(resume_text, job_description=None, template=None):
    """
    Analyzes a resume for ATS friendliness, skill gaps, role-specific weighting, 
    and resume risks using Groq AI.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"score": 0, "summary": "Missing API Key"}
    
    try:
        client = Groq(api_key=api_key)
    except Exception:
        return {"score": 0, "summary": "AI initialization failed."}

    MODEL_NAME = "llama-3.3-70b-versatile"
    
    role_weighting_context = ""
    if job_description:
        role_weighting_context = f"Job Description:\n{job_description}"

    template_instruction = ""
    if template == 'Google':
        template_instruction = "IMPORTANT: Use Google-style recruitment criteria. Prioritize metric-heavy achievements, data-driven results (e.g., 'increased X by Y%'), and clear impact summaries."
    elif template == 'Amazon':
        template_instruction = "IMPORTANT: Use Amazon-style recruitment criteria. Focus on Leadership Principles like 'Ownership', 'Deliver Results', and 'Bias for Action'. Ensure accomplishments follow the STAR (Situation, Task, Action, Result) method."
    elif template == 'Meta':
        template_instruction = "IMPORTANT: Use Meta-style recruitment criteria. Focus on product impact, moving fast, and end-to-end ownership of features. Highlight how your work improved user experience or business metrics."
    elif template == 'Microsoft':
        template_instruction = "IMPORTANT: Use Microsoft-style recruitment criteria. Emphasize technical depth, collaboration across teams, and long-term codebase health. Focus on architectural decisions and problem-solving."
    elif template == 'Apple':
        template_instruction = "IMPORTANT: Use Apple-style recruitment criteria. Focus on incredible attention to detail, simplicity, and the intersection of technology and liberal arts. Highlight perfection in craft."
    elif template == 'Netflix':
        template_instruction = "IMPORTANT: Use Netflix-style recruitment criteria. Focus on high-performance 'stunning colleagues', context over control, and radical candor in technical decisions. Highlight individual contribution to large-scale systems."
    elif template == 'Startups':
        template_instruction = "IMPORTANT: Use Startup/YC-style criteria. Focus on technical speed, traction, building things from scratch, and being a generalist who can wear multiple hats."

    prompt = f"""
    Analyze this resume for ATS friendliness.
    {role_weighting_context}
    {template_instruction}
    
    IMPORTANT: Do NOT use ANY emojis in your response. Keep the tone professional and text-based only.
    
    SCORING LOGIC:
    - If a resume explicitly includes and quantifies practically all skills/requirements from the JD, the score should be 95-100.
    - If there are minor gaps, score 80-90.
    - Do not be overly pedantic; if the skill is mentioned in a relevant context, count it as a match.
    
    Format response as JSON:
    "score": (0-100),
    "role_focus": (string),
    "matched_skills": [{{ "name": (str), "level": (str) }}],
    "detailed_skills": [{{ "name": (str), "level": (str), "score": (int 0-100) }}],
    "experience_match": [{{ "label": (str), "candidate": (str), "required": (str), "pct": (int 0-100) }}],
    "missing_skills": [(str)],
    "strengths": [(str)],
    "areas_to_develop": [(str)],
    "recommendation": (str),
    "risk_analysis": {{ "level": (str), "findings": [(str)] }},
    "roadmap": [(str)],
    "summary": (str),
    "tips": [(str)],
    "sample_ideal_resume": (CRITICAL: Generate a multi-section markdown resume that is a PERFECT 100% MATCH for this JD. It MUST explicitly include every single skill and requirement listed in the Job Description, using quantitative metrics like "Improved X by 30%". This sample is what the user will copy to get a 100 score.),
    "feedback_loop": {{ "current_percentile": (int), "gap_to_top_10": (int), "sections_to_improve": [] }}
    
    Resume:
    {resume_text}
    """
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": "You are an ATS expert that outputs JSON."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        # Using a simplified parse for now
        return json.loads(completion.choices[0].message.content)
    except Exception:
        return {"score": 0, "summary": "Analysis failed."}
