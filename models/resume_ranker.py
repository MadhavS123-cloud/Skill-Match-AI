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
    all_docs = [get_tokens(r) for r in resumes]
    jd_tokens = get_tokens(job_description)
    all_docs.append(jd_tokens)
    num_docs = len(all_docs)
    vocab = set(word for doc in all_docs for word in doc)
    doc_contains = Counter()
    for doc in all_docs:
        for word in set(doc):
            doc_contains[word] += 1
    idf = {word: math.log(num_docs / (1 + doc_contains[word])) for word in vocab}
    def get_tfidf_vec(tokens):
        tf = Counter(tokens)
        return {word: (count / len(tokens)) * idf[word] for word, count in tf.items() if word in idf}
    resume_vectors = [get_tfidf_vec(doc) for doc in all_docs[:-1]]
    jd_vector = get_tfidf_vec(jd_tokens)
    def cosine_sim(vec1, vec2):
        dot = sum(val * vec2[word] for word, val in vec1.items() if word in vec2)
        mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
        return dot / (mag1 * mag2) if mag1 and mag2 else 0
    results = [(i, [cosine_sim(r_vec, jd_vector)]) for i, r_vec in enumerate(resume_vectors)]
    return sorted(results, key=lambda x: x[1][0], reverse=True)
