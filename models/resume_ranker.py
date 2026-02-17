from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def rank_resumes(resumes, job_description):
    """
    Ranks resumes against a job description using lightweight TF-IDF.
    Hosting-friendly and credit-free.
    """
    if not resumes or not job_description:
        return []
        
    try:
        # We use n-grams (1,2) to capture some semantic context (e.g. "Software Engineer")
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        all_texts = [job_description] + resumes
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        jd_vector = tfidf_matrix[0:1]
        resume_vectors = tfidf_matrix[1:]
        
        # Calculate cosine similarity
        similarities = cosine_similarity(jd_vector, resume_vectors)[0]
        
        results = []
        for i, sim in enumerate(similarities):
            # Convert to float for JSON serialization
            score = float(sim)
            results.append((i, [score]))
            
        # Sort by score descending
        return sorted(results, key=lambda x: x[1][0], reverse=True)
        
    except Exception as e:
        print(f"Ranking error: {e}")
        # Final fallback
        results = []
        jd_words = set(job_description.lower().split())
        for i, resume in enumerate(resumes):
            res_words = set(resume.lower().split())
            intersection = jd_words.intersection(res_words)
            score = len(intersection) / len(jd_words) if jd_words else 0
            results.append((i, [score]))
        return sorted(results, key=lambda x: x[1][0], reverse=True)
