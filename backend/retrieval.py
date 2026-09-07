"""
Retrieval module using TF-IDF + cosine similarity.
Builds an in-memory index from corpus chunks and supports top-k search.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Optional
from backend.ingest import Chunk


class RetrievalResult:
    """A chunk with its similarity score."""
    def __init__(self, chunk: Chunk, score: float):
        self.section_id = chunk.section_id
        self.source_file = chunk.source_file
        self.text = chunk.text
        self.conflict_group = chunk.conflict_group
        self.score = round(float(score), 4)


class TFIDFRetriever:
    """TF-IDF based retriever with cosine similarity search."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.texts = [chunk.text for chunk in chunks]

        # Build TF-IDF index
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=10000,
            ngram_range=(1, 2),  # unigrams + bigrams for better matching
            sublinear_tf=True,
            min_df=1
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.texts)
        print(f"[retrieval] Built TF-IDF index: {self.tfidf_matrix.shape[0]} docs, "
              f"{self.tfidf_matrix.shape[1]} features")

    def search(self, query: str, top_k: int = 10) -> list[RetrievalResult]:
        """
        Search for the most relevant chunks for the given query.
        Returns top_k results sorted by cosine similarity score (descending).
        """
        if not query or not query.strip():
            return []

        # Transform query using the fitted vectorizer
        query_vec = self.vectorizer.transform([query])

        # Compute cosine similarity against all chunks
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get top-k indices sorted by score (descending)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append(RetrievalResult(
                chunk=self.chunks[idx],
                score=scores[idx]
            ))

        return results

    def get_all_scores(self, query: str) -> list[tuple[str, float]]:
        """
        Get scores for all chunks (useful for threshold tuning).
        Returns list of (section_id, score) sorted by score descending.
        """
        if not query or not query.strip():
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        indexed = [(self.chunks[i].section_id, float(scores[i])) for i in range(len(scores))]
        indexed.sort(key=lambda x: x[1], reverse=True)
        return indexed
