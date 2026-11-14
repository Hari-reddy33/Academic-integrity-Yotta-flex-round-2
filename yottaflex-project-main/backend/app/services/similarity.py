"""Local lexical similarity baseline used for human-review support."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compare_to_candidates(text: str, candidates: list[str]) -> tuple[float, int | None]:
    if not candidates:
        return 0.0, None
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=20_000)
    matrix = vectorizer.fit_transform([text, *candidates])
    scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    best_index = int(scores.argmax())
    return round(float(scores[best_index]), 4), best_index


def compare_text(text_a: str, text_b: str) -> dict:
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=20_000)
    matrix = vectorizer.fit_transform([text_a, text_b])
    score = float(cosine_similarity(matrix[0], matrix[1])[0, 0])
    terms = vectorizer.get_feature_names_out()
    weights_a = dict(zip(matrix[0].indices, matrix[0].data))
    weights_b = dict(zip(matrix[1].indices, matrix[1].data))
    common = [
        {"term": str(terms[index]), "weight": round(float(weights_a[index] * weights_b[index]), 4)}
        for index in weights_a.keys() & weights_b.keys()
    ]
    return {
        "score": round(score, 4),
        "shared_terms": sorted(common, key=lambda item: item["weight"], reverse=True)[:8],
    }

