from app.models.document_model import DocumentModel
from sqlalchemy import desc
import os
import uuid
import asyncio
from app.ingestions.pdf_loader import extract_pdf_to_text
from app.ingestions.text_splitting import creating_chunks
from app.ingestions.embeddings import create_embeddings
from app.vectorstore.chromadb_client import store_embeddings

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

async def post_document(document, user, db):
    unique_filename = f"{uuid.uuid4()}_{document.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        # Use await with document.read for async efficiency! 
        while chunk := await document.read(1024 * 1024):  # 1MB chunks
            f.write(chunk)

    new_doc = DocumentModel(
        file_name=document.filename,
        file_path=file_path,
        user_id=user.id
    )

    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return new_doc

async def process_document_background(file_path: str, user_id: int, document_id: int):
    # This runs in background to prevent timeout
    try:
        print(f"🔄 [UPLOAD] Starting background processing for doc_id: {document_id}")
        
        # CPU-heavy tasks must run in to_thread to prevent event loop blocking!
        text = await asyncio.to_thread(extract_pdf_to_text, file_path)
        chunks = await asyncio.to_thread(creating_chunks, text)
        
        # Parallel asynchronous embedding generation (uses HTTPX)
        print(f"⏳ [UPLOAD] Generating {len(chunks)} embeddings...")
        embeddings = await create_embeddings(chunks)
        
        # Synchronous DB operation must run in to_thread
        if embeddings:
            print("⏳ [UPLOAD] Storing embeddings in ChromaDB...")
            await asyncio.to_thread(
                store_embeddings,
                embeddings, # Not passed by name to avoid kwarg issues if store_embeddings signature differs
                user_id,
                document_id
            )
            print(f"✅ [UPLOAD] Successfully processed and stored {len(embeddings)} embeddings for doc_id: {document_id}")
        else:
            print(f"⚠️ [UPLOAD] No embeddings generated for doc_id: {document_id}")

    except Exception as e:
        print(f"❌ Error processing document in background: {e}")

def get_documents(user, db):
    if not user: return None
    documents = db.query(DocumentModel).filter(DocumentModel.user_id == user.id).order_by(desc(DocumentModel.created_at)).all()
    if not documents:
        return []
    return documents
