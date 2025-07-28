import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings

class DocumentRetriever:
    def __init__(self):
        """
        Initializes the retriever, loading the FAISS index and embedding model.
        """
        self.index_dir = os.path.join(settings.PROCESSED_DATA_DIR, "document")
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self._load_index()

    def _load_index(self):
        """
        Loads the FAISS index from disk if it exists.
        """
        index_path = os.path.join(self.index_dir, "faiss_index.bin")
        try:
            self.vector_store = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
            print(f"Loaded FAISS index from {index_path}")
        except Exception as e:
            self.vector_store = None
            print(f"Warning: Could not load FAISS index from {index_path}. Error: {e}. Please run the document processing endpoint first.")

    def retrieve(self, query: str, top_k: int = 5):
        """
        Performs a similarity search on the vector store.
        """
        if not self.vector_store:
            # Attempt to load the index on-the-fly if it wasn't available at startup
            self._load_index()
            if not self.vector_store:
                return {"error": "FAISS index is not available. Please process the documents first."}
            
        print(f"Retrieving documents for query: '{query}'")
        results = self.vector_store.similarity_search(query, k=top_k)
        return results
