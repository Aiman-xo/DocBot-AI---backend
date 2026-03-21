from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, status
from app.schemas.document_schema import PDFDocumentUploadResponse
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.services.pdf_service import post_document, get_documents, process_document_background

router = APIRouter(prefix='/document')

@router.post('/upload', response_model=PDFDocumentUploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks, 
    document: UploadFile = File(...), 
    user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Asynchronously save file and create DB entry
    new_doc = await post_document(document, user, db)
    
    if not new_doc:
        raise HTTPException(status_code=400, detail='Document not provided')
    
    # Run heavy processing (extraction, embeddings) in the background.
    # We use a Semaphore inside create_embeddings to prevent server crashes.
    background_tasks.add_task(
        process_document_background, 
        new_doc.file_path, 
        user.id, 
        new_doc.id
    )

    return {
        'message': 'Pdf Uploaded Successfully',
        'document': new_doc
    }

@router.get('/')
def retrieve_documents(user = Depends(get_current_user), db: Session = Depends(get_db)):
    documents = get_documents(user, db)
    return documents