import os
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from app.core.config import settings
from app.core.state import state_manager, ProcessingStatus

class DocumentIndexer:
    def __init__(self):
        self.doc_path = settings.USER_GUIDE_PATH
        self.output_dir = os.path.join(settings.PROCESSED_DATA_DIR, "document")
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

    def index(self):
        """
        Loads, processes, and indexes the document content into a FAISS vector store.
        """
        try:
            state_manager.set_status("document", ProcessingStatus.PROCESSING)
            print(f"Indexing document at {self.doc_path}...")
            os.makedirs(self.output_dir, exist_ok=True)

            with open(self.doc_path, 'r') as f:
                text = f.read()
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            docs = [Document(page_content=x) for x in text_splitter.split_text(text)]
            
            vector_store = FAISS.from_documents(docs, self.embeddings)
            
            index_path = os.path.join(self.output_dir, "faiss_index.bin")
            vector_store.save_local(index_path)
            
            print(f"Built and saved FAISS index with {vector_store.index.ntotal} documents to {index_path}.")
            state_manager.set_status("document", ProcessingStatus.READY)
            return True
        except Exception as e:
            print(f"Error during document indexing: {e}")
            state_manager.set_status("document", ProcessingStatus.ERROR)
            return False