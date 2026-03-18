from app.models.document_model import DocumentModel
from sqlalchemy import desc

import os
import uuid
from app.ingestions.pdf_loader import extract_pdf_to_text
from app.ingestions.text_splitting import creating_chunks
from app.ingestions.embeddings import create_embeddings
from app.vectorstore.chromadb_client import store_embeddings

UPLOAD_DIR = "uploads"

def post_document(document,user,db):

    unique_filename = f"{uuid.uuid4()}_{document.filename}"
    
    file_path = os.path.join(UPLOAD_DIR,unique_filename)

    with open(file_path,"wb") as f:
        f.write(document.file.read())

    
    new_doc = DocumentModel(
        file_name=document.filename,
        file_path=file_path,
        user_id=user.id
    )

    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    document.file.seek(0)

    text = extract_pdf_to_text(document)
    chunks = creating_chunks(text)
    embeddings = create_embeddings(chunks)
    store_embeddings(
        embeddings=embeddings,
        user_id=user.id,
        document_id=new_doc.id
    )

    return new_doc

def get_documents(user,db):
    if not user: return None
    documents = db.query(DocumentModel).filter(DocumentModel.user_id == user.id).order_by(desc(DocumentModel.created_at)).all()
    if not documents:
        return []
    return documents
