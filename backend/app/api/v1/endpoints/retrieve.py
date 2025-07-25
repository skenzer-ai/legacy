from fastapi import APIRouter, Depends, HTTPException
from app.core.retrieval.api.retriever import ApiRetriever
from app.core.retrieval.document.retriever import DocumentRetriever
from app.core.retrieval.fusion.fuser import Fuser
from app.core.state import state_manager, ProcessingStatus

router = APIRouter()

# Create singleton instances
api_retriever = ApiRetriever()
doc_retriever = DocumentRetriever()
fuser = Fuser()

def get_api_retriever():
    return api_retriever

def get_doc_retriever():
    return doc_retriever

def get_fuser():
    return fuser

@router.get("/document")
def retrieve_from_document(query: str, retriever: DocumentRetriever = Depends(get_doc_retriever)):
    """
    Endpoint to retrieve information from the user guide.
    """
    if state_manager.get_status("document") != ProcessingStatus.READY:
        raise HTTPException(status_code=400, detail="Document index is not ready. Please process the document first.")
    results = retriever.retrieve(query)
    return {"query": query, "source": "document", "results": results}

@router.get("/api")
def retrieve_from_api_spec(query: str, retriever: ApiRetriever = Depends(get_api_retriever)):
    """
    Endpoint to retrieve information from the API specification.
    """
    if state_manager.get_status("api") != ProcessingStatus.READY:
        raise HTTPException(status_code=400, detail="API spec index is not ready. Please process the API spec first.")
    results = retriever.retrieve(query)
    return {"query": query, "source": "api", "results": results}

@router.get("/fuse")
def retrieve_fused(
    query: str,
    api_retriever: ApiRetriever = Depends(get_api_retriever),
    doc_retriever: DocumentRetriever = Depends(get_doc_retriever),
    fuser: Fuser = Depends(get_fuser)
):
    """
    Endpoint to retrieve fused results from all available retrievers.
    """
    doc_status = state_manager.get_status("document")
    api_status = state_manager.get_status("api")

    if doc_status != ProcessingStatus.READY or api_status != ProcessingStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"One or more indexes are not ready. Document status: {doc_status.value}, API status: {api_status.value}"
        )

    api_results = api_retriever.retrieve(query)
    doc_results = doc_retriever.retrieve(query)
    
    fused_results = fuser.fuse([api_results, doc_results])
    
    return {"query": query, "source": "fused", "results": fused_results}