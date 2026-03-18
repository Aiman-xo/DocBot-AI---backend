from fastapi import APIRouter,Depends,UploadFile,File
from fastapi import HTTPException,status
from app.schemas.document_schema import PDFDocumentUploadResponse
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.services.pdf_service import post_document,get_documents



router = APIRouter(prefix='/document')


@router.post('/upload',response_model=PDFDocumentUploadResponse)
def upload_pdf(document : UploadFile = File(...),user=Depends(get_current_user),db:Session = Depends(get_db)):
    new_doc = post_document(document,user,db)
    if not new_doc:
        raise HTTPException(status_code=400,detail='Document not provided')
    
    return {
        'message':'Pdf Uploaded Successfully',
        'document':new_doc
    }

@router.get('/')
def retrieve_documents(user=Depends(get_current_user),db:Session=Depends(get_db)):
    documents = get_documents(user,db)
    
    return documents