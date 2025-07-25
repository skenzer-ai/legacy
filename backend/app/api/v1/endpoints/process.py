from fastapi import APIRouter, HTTPException
from app.core.processing.api.indexer import ApiIndexer
from app.core.processing.document.indexer import DocumentIndexer
from app.core.state import state_manager, ProcessingStatus

router = APIRouter()

@router.post("/document")
def process_document():
    """
    Endpoint to trigger the processing and indexing of the user guide.
    This is now a synchronous operation.
    """
    if state_manager.get_status("document") == ProcessingStatus.PROCESSING:
        raise HTTPException(status_code=409, detail="Document processing is already in progress.")
    
    indexer = DocumentIndexer()
    if indexer.index():
        return {"message": "Document processing completed successfully."}
    else:
        raise HTTPException(status_code=500, detail="Document processing failed.")

@router.post("/api")
def process_api_spec():
    """
    Endpoint to trigger the processing and indexing of the API specification.
    This is now a synchronous operation.
    """
    if state_manager.get_status("api") == ProcessingStatus.PROCESSING:
        raise HTTPException(status_code=409, detail="API spec processing is already in progress.")

    indexer = ApiIndexer()
    if indexer.index():
        return {"message": "API spec processing completed successfully."}
    else:
        raise HTTPException(status_code=500, detail="API spec processing failed.")