def expand_job_requirements(input_text):
    """
    Expands a job title into a JD using deterministic templates (Credit-free).
    """
    templates = {
        "software engineer": "Software Engineer: Develop high-scale applications using Java/Python/Node.js. Experience with cloud (AWS/Azure), databases (SQL/NoSQL), and CI/CD. BS in CS or equivalent.",
        "backend engineer": "Backend Engineer: Design and implement scalable APIs and microservices. Expert in Python, Go, or Java. Familiarity with distributed systems and database optimization.",
        "frontend engineer": "Frontend Engineer: Build responsive UIs with React, Vue, or Angular. Strong JS/TS skills. Focus on performance, accessibility (A11y), and state management.",
        "product manager": "Product Manager: Define product roadmap and strategy. Strong communication skills. Data-driven decision making. Agile/Scrum experience.",
        "data scientist": "Data Scientist: Analyze complex datasets. Build and deploy ML models (Scikit-learn, PyTorch). Expert in Python/R and SQL. Statistical modeling proficiency.",
        "devops engineer": "DevOps Engineer: Manage cloud infrastructure and CI/CD pipelines. Expert in Kubernetes, Docker, and Terraform. Focus on reliability and security.",
    }
    
    input_lower = input_text.lower()
    
    # If it's already a full JD (long text), don't expand
    if len(input_text.split()) > 20:
        return input_text, False
        
    for title, jd in templates.items():
        if title in input_lower:
            return jd, True
            
    # Generic Expansion if no match
    return f"{input_text}: Requires strong domain knowledge, relevant technical skills, and proven experience delivering results in this role.", False
