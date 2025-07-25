import os
import pickle
from collections import defaultdict
from pyroaring import BitMap as Roaring
from sentence_transformers import CrossEncoder

from app.core.config import settings
from app.core.processing.api.tokenizers import CanonicalTokenizer

class ApiRetriever:
    """
    A multi-stage retriever for searching the API specification.
    """
    def __init__(self):
        self.index_dir = os.path.join(settings.PROCESSED_DATA_DIR, "api")
        self.tokenizer = CanonicalTokenizer()
        self.inverted_index = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.full_text_cache = None
        self._load_indices()
        self.cross_encoder = CrossEncoder(settings.CROSS_ENCODER_MODEL)

    def _load_indices(self):
        """
        Loads the retrieval indices from disk if they exist.
        """
        print(f"Attempting to load API indices from {self.index_dir}...")
        try:
            # Load bitmap index
            with open(os.path.join(self.index_dir, "bitmap_index.bin"), "rb") as f:
                self.inverted_index = pickle.load(f)

            # Load TF-IDF vectorizer and matrix
            with open(os.path.join(self.index_dir, "tfidf_vectorizer.pkl"), "rb") as f:
                self.tfidf_vectorizer = pickle.load(f)
            with open(os.path.join(self.index_dir, "tfidf_matrix.pkl"), "rb") as f:
                self.tfidf_matrix = pickle.load(f)

            # Load full-text cache
            with open(os.path.join(self.index_dir, "full_text_cache.pkl"), "rb") as f:
                self.full_text_cache = pickle.load(f)
            print("API indices loaded successfully.")
        except FileNotFoundError:
            print("API index files not found. Please run the API processing endpoint first.")

    def _get_candidates(self, query: str, top_k: int = 20):
        """
        Gets a set of candidate documents from the inverted index.
        """
        query_tokens = self.tokenizer.tokenize(query)
        if not query_tokens:
            return []

        token_bitmaps = [self.inverted_index.get(token, Roaring()) for token in query_tokens]
        
        candidate_scores = defaultdict(int)
        intersection_bitmap = Roaring.intersection(*token_bitmaps)
        for doc_id in intersection_bitmap:
            candidate_scores[doc_id] += 100

        union_bitmap = Roaring.union(*token_bitmaps)
        for doc_id in union_bitmap:
            for token_bitmap in token_bitmaps:
                if doc_id in token_bitmap:
                    candidate_scores[doc_id] += 1

        if not candidate_scores:
            query_vec = self.tfidf_vectorizer.transform([query])
            scores = (query_vec * self.tfidf_matrix.T).toarray()[0]
            top_tfidf_candidates = scores.argsort()[-top_k:][::-1]
            return list(top_tfidf_candidates)

        sorted_candidates = sorted(candidate_scores.items(), key=lambda item: item[1], reverse=True)
        return [doc_id for doc_id, score in sorted_candidates[:top_k]]

    def _rerank_candidates(self, query: str, candidates: list):
        """
        Reranks the candidates using a more powerful model.
        """
        if not candidates:
            return []

        candidate_docs = [self.full_text_cache[doc_id] for doc_id in candidates]
        cross_encoder_inputs = [[query, str(doc)] for doc in candidate_docs]
        scores = self.cross_encoder.predict(cross_encoder_inputs)
        ranked_candidates = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
        return [candidate for score, candidate in ranked_candidates]

    def retrieve(self, query: str, top_k: int = 5):
        """
        Performs a multi-stage search for the given query.
        """
        print(f"Retrieving API specs for query: '{query}'")
        if self.inverted_index is None or self.tfidf_vectorizer is None or self.tfidf_matrix is None or self.full_text_cache is None:
            # Attempt to load the index on-the-fly if it wasn't available at startup
            self._load_indices()
            if self.inverted_index is None or self.tfidf_vectorizer is None or self.tfidf_matrix is None or self.full_text_cache is None:
                return {"error": "API index is not available. Please process the API spec first."}

        candidates = self._get_candidates(query)
        reranked_candidates = self._rerank_candidates(query, candidates)
        
        return [self.full_text_cache[doc_id] for doc_id in reranked_candidates[:top_k]]