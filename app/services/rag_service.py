from app.models.document_model import DocumentModel
from app.vectorstore.chromadb_client import query_embeddings
from app.core.config import settings
from fastapi import HTTPException
import asyncio
import httpx


# LIGHTWEIGHT REST API APPROACH
# Instead of importing the heavy 'google-generativeai' SDK (which uses 100MB+ RAM),
# we call the Gemini API directly via HTTPX to stay under Render's 512MB limit.

async def get_embedding_rest(text: str):
    """Get embedding using Gemini REST API (Low memory)"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]},
        "task_type": "RETRIEVAL_QUERY"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["embedding"]["values"]
        except Exception as e:
            
            raise HTTPException(status_code=500, detail="Failed to get question embedding.")

async def generate_content_rest(prompt: str):
    """Generate content using Gemini REST API (Low memory)"""
    # Using gemini-3.1-flash-lite-preview: Extremely fast, lightweight preview model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "system_instruction": {
            "parts": [{"text": "You are a specialized document analyzer. You always respond with structured Markdown, using headers and bullet points. Never mention 'Based on the provided context'—just provide the answer directly and professionally."}]
        },
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.8,
            "topK": 40
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            # extracts the text 
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except httpx.HTTPStatusError as e:
            print(f"Gemini API Status Error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=500, detail="Failed to generate AI response.")
        except Exception as e:
            print(f"Gemini API Exception: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate AI response.")


async def ask_question(request, db, user):
    
    question = request.question
    document_id = request.document_id

    # Offload synchronous DB query to a separate thread
    doc = await asyncio.to_thread(
        db.query(DocumentModel).filter(
            DocumentModel.id == document_id, 
            DocumentModel.user_id == user.id
        ).first
    )

    if not doc:
        
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    print(f"✅ [RAG] Found Document in SQL: {doc.id}")

    # Get question embedding with the lightweight REST approach
    requested_question_embedding = await get_embedding_rest(question)
    # ChromaDB query (wrapped in to_thread to prevent blocking)
    results = await asyncio.to_thread(
        query_embeddings,
        query_embeddings=[requested_question_embedding],
        n_results=5,
        where={
            "$and": [
                {"user_id": user.id},
                {"document_id": document_id}
            ]
        }
    )

    # extracts the text 
    chunks = results.get("documents", [[]])[0] if results and "documents" in results else []
    
    if not chunks:
        context = "No document content is currently available. If the user asks about the document, inform them that the document appears to be empty or is still processing."
    else:
        context = "\n".join(chunks)

    prompt = f"""
        You are a friendly and professional AI Document Assistant. 
        
        INSTRUCTIONS:
        1. If the user's input is a casual greeting (like "hi", "hello", "what's up"), respond politely and ask how you can help them with their document.
        2. If the user asks a question about the document, you MUST answer it using ONLY the provided context below.
        3. If the answer is not in the context, say: "I'm sorry, but the document does not contain information regarding this topic."

        CONTEXT FROM DOCUMENT:
        {context}

        USER QUESTION:
        {question}

        FORMATTING INSTRUCTIONS:
        1. Use **Markdown** for clarity.
        2. Use ## for section headings if the answer is long.
        3. Use bullet points for lists.
        4. Use **bold text** for key terms.
        5. Tone: Professional, helpful, and concise.
    """
    # Generate content with the lightweight REST approach
    answer_text = await generate_content_rest(prompt)
    
    return {
        "answer": answer_text
    }
