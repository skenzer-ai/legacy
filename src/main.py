from fastapi import FastAPI
from pydantic import BaseModel

from src.retrieval.retriever import KnowledgeRetriever

app = FastAPI()
retriever = KnowledgeRetriever()

class SearchQuery(BaseModel):
    query: str

@app.post("/search")
def search(query: SearchQuery):
    return retriever.search(query.query)
