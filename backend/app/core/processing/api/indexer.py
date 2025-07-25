import json
import os
import pickle
from collections import defaultdict
from pyroaring import BitMap as Roaring
from sklearn.feature_extraction.text import TfidfVectorizer

from app.core.config import settings
from .tokenizers import CanonicalTokenizer
from app.core.state import state_manager, ProcessingStatus

class ApiIndexer:
    def __init__(self):
        self.api_spec_path = settings.API_SPEC_PATH
        self.output_dir = os.path.join(settings.PROCESSED_DATA_DIR, "api")
        self.tokenizer = CanonicalTokenizer()

    def index(self):
        """
        Loads the API specification, processes it, and builds the
        TF-IDF and Roaring Bitmap indices.
        """
        try:
            state_manager.set_status("api", ProcessingStatus.PROCESSING)
            print(f"Indexing API spec from {self.api_spec_path}...")
            os.makedirs(self.output_dir, exist_ok=True)

            # 1. Load Raw Data
            with open(self.api_spec_path, 'r') as f:
                api_spec = json.load(f)

            # Data Processing
            processed_docs = []
            for i, endpoint in enumerate(api_spec):
                path = endpoint.get("path", "")
                operation_id = endpoint.get("operationId", "")
                description = endpoint.get("description", "")
                summary = endpoint.get("summary", "")
                tags = " ".join(endpoint.get("tags", []))
                full_text = f"{path} {operation_id} {tags} {summary} {description}"
                tokens = self.tokenizer.tokenize(full_text)
                
                expanded_tokens = set(tokens)
                if operation_id:
                    expanded_tokens.add(operation_id)

                processed_docs.append({
                    "doc_id": i,
                    "endpoint": endpoint,
                    "tokens": list(expanded_tokens),
                    "full_text_for_tfidf": " ".join(expanded_tokens)
                })

            # Build Inverted Index (Roaring Bitmaps)
            inverted_index = defaultdict(Roaring)
            for doc in processed_docs:
                for token in doc["tokens"]:
                    inverted_index[token].add(doc["doc_id"])

            bitmap_index_path = os.path.join(self.output_dir, "bitmap_index.bin")
            with open(bitmap_index_path, 'wb') as f:
                pickle.dump(inverted_index, f)

            # Build TF-IDF Index
            tfidf_vectorizer = TfidfVectorizer()
            tfidf_matrix = tfidf_vectorizer.fit_transform([doc['full_text_for_tfidf'] for doc in processed_docs])

            tfidf_vectorizer_path = os.path.join(self.output_dir, "tfidf_vectorizer.pkl")
            with open(tfidf_vectorizer_path, 'wb') as f:
                pickle.dump(tfidf_vectorizer, f)
            
            tfidf_matrix_path = os.path.join(self.output_dir, "tfidf_matrix.pkl")
            with open(tfidf_matrix_path, 'wb') as f:
                pickle.dump(tfidf_matrix, f)

            # Build Full-Text Cache
            full_text_cache = {doc['doc_id']: doc['endpoint'] for doc in processed_docs}
            full_text_cache_path = os.path.join(self.output_dir, "full_text_cache.pkl")
            with open(full_text_cache_path, 'wb') as f:
                pickle.dump(full_text_cache, f)

            print("API spec indexing complete.")
            state_manager.set_status("api", ProcessingStatus.READY)
            return True
        except Exception as e:
            print(f"Error during API spec indexing: {e}")
            state_manager.set_status("api", ProcessingStatus.ERROR)
            return False