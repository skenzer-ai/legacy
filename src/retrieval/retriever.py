import os
import pickle
from typing import List, Tuple
from langchain_core.documents import Document
from .api_retriever import APIRetriever
from .document_retriever import DocumentRetriever
from ..processing.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeRetriever:
    def __init__(self, index_dir: str = "dist"):
        logger.info("Initializing KnowledgeRetriever...")

        self.api_retriever = APIRetriever(index_dir=index_dir)
        # This will need to be implemented properly later
        self.doc_retriever = DocumentRetriever()

        logger.info("KnowledgeRetriever initialized successfully.")

    def search(self, query: str, k: int = 5) -> List[Document]:
        logger.info(f"Performing search for query: '{query}'")

        # 1. Parallel Search
        api_docs = self.api_retriever.search(query, top_k=k)
        logger.info(f"API retriever found {len(api_docs)} results.")
        
        doc_results = []
        if self.doc_retriever:
            doc_results = self.doc_retriever.search(query, top_k=k)
        logger.info(f"Document retriever found {len(doc_results)} results.")

        # Combine and remove duplicates
        final_results = []
        seen_api_results = set()
        seen_doc_results = set()

        for doc in api_docs:
            doc_str = str(doc)
            if doc_str not in seen_api_results:
                final_results.append(doc)
                seen_api_results.add(doc_str)

        for doc in doc_results:
            if doc.page_content not in seen_doc_results:
                final_results.append(doc)
                seen_doc_results.add(doc.page_content)
        
        logger.info(f"Final results count: {len(final_results)}")
        return final_results
