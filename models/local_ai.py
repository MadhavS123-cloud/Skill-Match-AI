import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import ollama

# Singleton for local embedding model
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        # Using a lightweight, fast model suitable for local deployment
        try:
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            return None
    return _embedding_model

def get_embeddings(texts):
    model = get_embedding_model()
    if model is None:
        return None
    return model.encode(texts)

def calculate_similarity(text1, text2):
    embeddings = get_embeddings([text1, text2])
    if embeddings is None:
        return 0.0
    return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])

def call_local_llm(prompt, system_prompt="You are a helpful career assistant."):
    """
    Calls Ollama locally. Requires Ollama to be installed and running.
    """
    try:
        response = ollama.chat(model='llama3', messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt},
        ])
        return response['message']['content']
    except Exception as e:
        print(f"Ollama call failed: {e}")
        return "Local LLM service (Ollama) is not reachable. Please ensure Ollama is installed and running with 'llama3' model."

def extract_skills_locally(text):
    """
    Extracts common tech skills using regex (fast/deterministic fallback).
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
    Checks for required skills in resume using semantic similarity.
    This helps find "Backend" if resume says "Server-side", etc.
    """
    if not required_skills:
        return [], []
        
    resume_sentences = re.split(r'[.\n]', resume_text)
    resume_sentences = [s.strip() for s in resume_sentences if len(s.strip()) > 10]
    
    if not resume_sentences:
        return [], required_skills
        
    model = get_embedding_model()
    if not model:
        # Fallback to simple keyword match
        found = []
        missing = []
        for s in required_skills:
            if s.lower() in resume_text.lower(): found.append(s)
            else: missing.append(s)
        return found, missing

    # Semantic matching logic
    required_embeddings = model.encode(required_skills)
    resume_embeddings = model.encode(resume_sentences)
    
    similarities = cosine_similarity(required_embeddings, resume_embeddings)
    
    found = []
    missing = []
    
    for i, skill in enumerate(required_skills):
        best_match_score = np.max(similarities[i])
        if best_match_score > 0.6: # Threshold for semantic match
            found.append(skill)
        else:
            missing.append(skill)
            
    return found, missing
