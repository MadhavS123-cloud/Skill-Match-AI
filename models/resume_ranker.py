import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z ]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def rank_resumes(resumes, job_description):
    cleaned_resumes = [clean_text(r) for r in resumes]
    cleaned_jd = clean_text(job_description)

    documents = cleaned_resumes + [cleaned_jd]

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(documents)

    resume_vectors = tfidf_matrix[:-1]
    jd_vector = tfidf_matrix[-1]

    scores = cosine_similarity(resume_vectors, jd_vector)

    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1][0],
        reverse=True
    )

    return ranked
