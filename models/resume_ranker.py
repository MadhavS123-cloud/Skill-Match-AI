import re
import math
from collections import Counter

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z ]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_tokens(text):
    return clean_text(text).split()

def rank_resumes(resumes, job_description):
    """
    Pure Python implementation of TF-IDF and Cosine Similarity
    to avoid heavy sklearn dependency on Vercel.
    """
    # 1. Tokenize all documents
    all_docs = [get_tokens(r) for r in resumes]
    jd_tokens = get_tokens(job_description)
    all_docs.append(jd_tokens)
    
    num_docs = len(all_docs)
    
    # 2. Calculate IDF
    # Count how many documents contain each word
    vocab = set(word for doc in all_docs for word in doc)
    doc_contains = Counter()
    for doc in all_docs:
        unique_words = set(doc)
        for word in unique_words:
            doc_contains[word] += 1
            
    idf = {}
    for word in vocab:
        # Standard IDF: log(N / (1 + df))
        idf[word] = math.log(num_docs / (1 + doc_contains[word]))
        
    # 3. Calculate TF-IDF vectors for documents
    def get_tfidf_vec(tokens):
        tf = Counter(tokens)
        vec = {}
        for word, count in tf.items():
            if word in idf:
                vec[word] = (count / len(tokens)) * idf[word]
        return vec

    resume_vectors = [get_tfidf_vec(doc) for doc in all_docs[:-1]]
    jd_vector = get_tfidf_vec(jd_tokens)
    
    # 4. Cosine Similarity
    def cosine_sim(vec1, vec2):
        # dot product
        dot = 0
        for word, val in vec1.items():
            if word in vec2:
                dot += val * vec2[word]
        
        # magnitudes
        mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0
        return dot / (mag1 * mag2)

    results = []
    for i, r_vec in enumerate(resume_vectors):
        score = cosine_sim(r_vec, jd_vector)
        # Format as [[score]] to match previous API expectation if needed,
        # but the previous code used ranked[index][1][0]. 
        # Actually previous code: scores = cosine_similarity(resume_vectors, jd_vector)
        # which returns a 2D array.
        results.append((i, [score]))

    # 5. Rank
    ranked = sorted(
        results,
        key=lambda x: x[1][0],
        reverse=True
    )

    return ranked
