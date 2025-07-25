import pickle
from pyroaring import BitMap as Roaring
from collections import defaultdict
from src.processing.tokenizers import CanonicalTokenizer
from sentence_transformers import CrossEncoder
from src.processing.config import settings

class APIRetriever:
    """
    A multi-stage retriever for searching the API specification.
    """
    def __init__(self, index_dir: str = "dist"):
        self.index_dir = index_dir
        self.tokenizer = CanonicalTokenizer()
        self._load_indices()
        self.cross_encoder = CrossEncoder(settings.cross_encoder_model_name)

    def _load_indices(self):
        """
        Loads the retrieval indices from disk.
        """
        # Load bitmap index
        with open(f"{self.index_dir}/bitmap_index.bin", "rb") as f:
            self.inverted_index = pickle.load(f)

        # Load TF-IDF vectorizer and matrix
        with open(f"{self.index_dir}/tfidf_vectorizer.pkl", "rb") as f:
            self.tfidf_vectorizer = pickle.load(f)
        with open(f"{self.index_dir}/tfidf_matrix.pkl", "rb") as f:
            self.tfidf_matrix = pickle.load(f)

        # Load full-text cache
        with open(f"{self.index_dir}/full_text_cache.pkl", "rb") as f:
            self.full_text_cache = pickle.load(f)

    def get_candidates(self, query: str, top_k: int = 20):
        """
        Gets a set of candidate documents from the inverted index.
        """
        query_tokens = self.tokenizer.tokenize(query)
        
        if not query_tokens:
            return []

        # Add the raw query to the tokens to boost exact matches
        query_tokens.append(query)

        # Retrieve the bitmaps for each token
        token_bitmaps = [self.inverted_index.get(token, Roaring()) for token in query_tokens]

        # --- Weighted Voting using Bitmaps ---
        # For simplicity, we'll use the intersection as a base score
        candidate_scores = defaultdict(int)
        
        # Intersection of all tokens gives a high score
        intersection_bitmap = Roaring.intersection(*token_bitmaps)
        for doc_id in intersection_bitmap:
            candidate_scores[doc_id] += 100 # High score for matching all tokens

        # Union of all tokens
        union_bitmap = Roaring.union(*token_bitmaps)
        
        # Add scores for each token match
        for doc_id in union_bitmap:
            for token_bitmap in token_bitmaps:
                if doc_id in token_bitmap:
                    candidate_scores[doc_id] += 1

        if not candidate_scores:
            # --- Fallback to TF-IDF if no candidates from bitmaps ---
            query_vec = self.tfidf_vectorizer.transform([query])
            scores = (query_vec * self.tfidf_matrix.T).toarray()[0]
            
            # Get the top_k candidates from TF-IDF
            top_tfidf_candidates = scores.argsort()[-top_k:][::-1]
            return list(top_tfidf_candidates)

        # Sort candidates by score
        sorted_candidates = sorted(candidate_scores.items(), key=lambda item: item[1], reverse=True)
        
        return [doc_id for doc_id, score in sorted_candidates[:top_k]]

    def rerank_candidates(self, query: str, candidates: list):
        """
        Reranks the candidates using a more powerful model.
        """
        if not candidates:
            return []

        # Fetch full text for each candidate
        candidate_docs = [self.full_text_cache[doc_id] for doc_id in candidates]

        # Prepare inputs for the cross-encoder
        cross_encoder_inputs = [[query, str(doc)] for doc in candidate_docs]

        # Get scores from the cross-encoder
        scores = self.cross_encoder.predict(cross_encoder_inputs)

        # Combine candidates with their scores and sort
        ranked_candidates = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)

        return [candidate for score, candidate in ranked_candidates]

    def apply_guardrails(self, query: str, ranked_endpoints: list):
        """
        Applies guardrails to the candidates.
        
        For now, this is a placeholder.
        """
        return ranked_endpoints

    def search(self, query: str, top_k: int = 5):
        """
        Performs a multi-stage search for the given query.
        """
        candidates = self.get_candidates(query)
        reranked_candidates = self.rerank_candidates(query, candidates)
        final_candidates = self.apply_guardrails(query, reranked_candidates)
        
        # Return the actual documents from the cache
        return [self.full_text_cache[doc_id] for doc_id in final_candidates[:top_k]]