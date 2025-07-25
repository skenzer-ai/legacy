from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from src.processing.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentRetriever:
    """
    A retriever for searching the document store.
    """
    def __init__(self, doc_path: str = "user_docs/infraon_user_guide.md"):
        self.doc_path = doc_path
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.api_embedding_model_name)
        self._build_index()

    def _build_index(self):
        """
        Builds the FAISS index from the document.
        """
        with open(self.doc_path, 'r') as f:
            text = f.read()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = [Document(page_content=x) for x in text_splitter.split_text(text)]
        
        self.index = FAISS.from_documents(docs, self.embeddings)
        logger.info(f"Built FAISS index with {self.index.index.ntotal} documents.")

    def search(self, query: str, top_k: int = 5):
        """
        Searches the document store for the given query.
        """
        logger.info(f"Searching for query: '{query}'")
        results = self.index.similarity_search(query, k=top_k)
        logger.info(f"Found {len(results)} results.")
        return results