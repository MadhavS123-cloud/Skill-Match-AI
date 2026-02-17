from .local_ai import get_embeddings
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def rank_resumes(resumes, job_description):
    """
    Ranks resumes against a job description using local SBERT embeddings.
    """
    if not resumes or not job_description:
        return []
        
    texts = [job_description] + resumes
    embeddings = get_embeddings(texts)
    
    if embeddings is None:
        # Fallback to a simple keyword-based ranking if embeddings fail
        print("Warning: Semantic embedding failed. Falling back to simple matching.")
        results = []
        jd_words = set(job_description.lower().split())
        for i, resume in enumerate(resumes):
            res_words = set(resume.lower().split())
            intersection = jd_words.intersection(res_words)
            score = len(intersection) / len(jd_words) if jd_words else 0
            results.append((i, [score]))
        return sorted(results, key=lambda x: x[1][0], reverse=True)

    jd_vector = embeddings[0].reshape(1, -1)
    resume_vectors = embeddings[1:]
    
    # Calculate cosine similarity
    similarities = cosine_similarity(jd_vector, resume_vectors)[0]
    
    results = []
    for i, sim in enumerate(similarities):
        # Convert to 0-100 scale
        score = float(sim)
        results.append((i, [score]))
        
    # Sort by score descending
    return sorted(results, key=lambda x: x[1][0], reverse=True)
