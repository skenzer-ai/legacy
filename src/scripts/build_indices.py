import argparse
import json
import os
import pickle
from collections import defaultdict
from pyroaring import BitMap as Roaring
from sklearn.feature_extraction.text import TfidfVectorizer
from src.processing.tokenizers import CanonicalTokenizer

def main(output_dir="dist", api_spec_path="user_docs/infraon-api.json", synonyms_path="src/retrieval/synonyms.json"):
    """
    Main function to build all retrieval indices from the API specification.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # 1. Load Raw Data
    print("Loading raw data...")
    with open(api_spec_path, 'r') as f:
        api_spec = json.load(f)
    
    with open(synonyms_path, 'r') as f:
        synonyms = json.load(f)

    print(f"Loaded {len(api_spec)} API paths.")
    print(f"Loaded {len(synonyms)} synonym groups.")

    # Initialize tokenizer and data structures
    tokenizer = CanonicalTokenizer()
    
    # --- Data Processing ---
    processed_docs = []
    for i, endpoint in enumerate(api_spec):
        # Combine relevant text fields
        path = endpoint.get("path", "")
        operation_id = endpoint.get("operationId", "")
        description = endpoint.get("description", "")
        summary = endpoint.get("summary", "")
        tags = " ".join(endpoint.get("tags", []))

        full_text = f"{path} {operation_id} {tags} {summary} {description}"
        
        # Tokenize and expand synonyms
        tokens = tokenizer.tokenize(full_text)
        
        expanded_tokens = set(tokens)
        for token in tokens:
            if token in synonyms:
                expanded_tokens.update(synonyms[token])
        
        # Add the original operationId to the tokens
        if operation_id:
            expanded_tokens.add(operation_id)

        processed_docs.append({
            "doc_id": i,
            "endpoint": endpoint,
            "tokens": list(expanded_tokens),
            "full_text_for_tfidf": " ".join(expanded_tokens)
        })

    print(f"Processed {len(processed_docs)} documents.")

    # --- Build Inverted Index (Roaring Bitmaps) ---
    print("Building roaring bitmap index...")
    inverted_index = defaultdict(Roaring)
    for doc in processed_docs:
        for token in doc["tokens"]:
            inverted_index[token].add(doc["doc_id"])

    # Save the inverted index
    bitmap_index_path = os.path.join(output_dir, "bitmap_index.bin")
    with open(bitmap_index_path, 'wb') as f:
        pickle.dump(inverted_index, f)
    print(f"Saved bitmap index to {bitmap_index_path}")

    # --- Build TF-IDF Index ---
    print("Building TF-IDF index...")
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform([doc['full_text_for_tfidf'] for doc in processed_docs])

    # Save the TF-IDF vectorizer and matrix
    tfidf_vectorizer_path = os.path.join(output_dir, "tfidf_vectorizer.pkl")
    tfidf_matrix_path = os.path.join(output_dir, "tfidf_matrix.pkl")
    with open(tfidf_vectorizer_path, 'wb') as f:
        pickle.dump(tfidf_vectorizer, f)
    with open(tfidf_matrix_path, 'wb') as f:
        pickle.dump(tfidf_matrix, f)
    print(f"Saved TF-IDF vectorizer to {tfidf_vectorizer_path}")
    print(f"Saved TF-IDF matrix to {tfidf_matrix_path}")

    # --- Build Full-Text Cache ---
    print("Building full-text cache...")
    full_text_cache = {doc['doc_id']: doc['endpoint'] for doc in processed_docs}
    
    full_text_cache_path = os.path.join(output_dir, "full_text_cache.pkl")
    with open(full_text_cache_path, 'wb') as f:
        pickle.dump(full_text_cache, f)
    print(f"Saved full-text cache to {full_text_cache_path}")

    print("\nIndexing pipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build retrieval indices from an OpenAPI specification.")
    parser.add_argument("--api_spec_path", type=str, default="user_docs/infraon-api.json", help="Path to the OpenAPI JSON file.")
    parser.add_argument("--synonyms_path", type=str, default="src/retrieval/synonyms.json", help="Path to the synonyms JSON file.")
    parser.add_argument("--output_dir", type=str, default="dist", help="Directory to save the output index files.")
    
    args = parser.parse_args()
    main(args.output_dir, args.api_spec_path, args.synonyms_path)
