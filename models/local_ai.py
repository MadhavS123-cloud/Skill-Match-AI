import os
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ollama

def calculate_similarity(text1, text2):
    """
    Calculates similarity using lightweight TF-IDF (Credit-free & Hosting-friendly).
    """
    try:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        return float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
    except:
        return 0.0

def call_local_llm(prompt, system_prompt="You are a helpful career assistant."):
    """
    Calls Ollama locally. Requires Ollama to be installed and running on the host.
    """
    try:
        # Note: This will only work if the host has Ollama installed. 
        # On cloud hosting like Render, this will safely fail and trigger fallbacks.
        response = ollama.chat(model='llama3', messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt},
        ])
        return response['message']['content']
    except:
        return "Local LLM service (Ollama) is not reachable. Using deterministic fallback logic."

def extract_skills_locally(text):
    """
    Extracts common tech skills using logic (fast/deterministic).
    """
    common_skills = [
        "Python", "JavaScript", "Java", "C++", "C#", "React", "Angular", "Vue", "Node.js", 
        "AWS", "Azure", "GCP", "Kubernetes", "Docker", "SQL", "NoSQL", "MongoDB", "PostgreSQL",
        "Machine Learning", "AI", "Cloud Computing", "DevOps", "Microservices", "REST API",
        "GraphQL", "TypeScript", "Go", "Rust", "Swift", "Kotlin", "TensorFlow", "PyTorch",
        "Pandas", "Scikit-learn", "Hadoop", "Spark", "Tableau", "PowerBI", "Agile", "Scrum"
    ]
    found = []
    text_upper = text.upper()
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill.upper()) + r'\b', text_upper):
            found.append(skill)
    return found

def match_skills_semantic(resume_text, required_skills):
    """
    Checks for required skills in resume using lightweight matching.
    """
    if not required_skills:
        return [], []
        
    found = []
    missing = []
    
    resume_lower = resume_text.lower()
    
    for skill in required_skills:
        # Simple but effective keyword match for hosting environments
        if skill.lower() in resume_lower:
            found.append(skill)
        else:
            missing.append(skill)
            
    return found, missing
