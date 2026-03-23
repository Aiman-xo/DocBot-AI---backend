from app.models.document_model import DocumentModel
from app.vectorstore.chromadb_client import collection
from app.ingestions.embeddings import create_embeddings
from app.core.config import settings
from fastapi import HTTPException
import google.generativeai as genai
import asyncio


genai.configure(api_key=settings.GEMINI_API_KEY)

# LAZY LOADING: We don't initialize the model globally. 
# This prevents the server from crashing or hanging during the initial 2-minute Render bootup on 512MB RAM.
_model_instance = None

def get_chat_model():
    global _model_instance
    if _model_instance is None:
        # Using gemini-3.1-flash (gemini-flash-latest) which is the most stable and fast model for RAG.
        _model_instance = genai.GenerativeModel(
            model_name="gemini-flash-latest", 
            system_instruction="You are a specialized document analyzer. You always respond with structured Markdown," \
                               " using headers and bullet points. Never mention 'Based on the provided context'—just provide the answer directly and professionally."
        )
    return _model_instance



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

    # Get question embedding with retrieval_query task type for better accuracy
    # Using gemini-embedding-001 for maximum compatibility
    try:
        question_embedding_data = await genai.embed_content_async(
            model="models/gemini-embedding-001",
            content=question,
            task_type="retrieval_query"
        )
        requested_question_embedding = question_embedding_data["embedding"]
    except Exception as e:
        print(f"❌ Error during embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to process question embedding.")

    # ChromaDB query (wrapped in to_thread to prevent blocking the single-worker server)
    results = await asyncio.to_thread(
        collection.query,
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
    chunks = results.get("documents", [[]])[0]
    
    if not chunks:
        return {"answer": "I'm sorry, I couldn't find any relevant information in the selected document to answer your question."}

    # joins all to create context string
    context = "\n".join(chunks)


    prompt = f"""
        You are a professional AI Document Assistant. 
        Your goal is to answer the user's question using ONLY the provided context.

        CONTEXT FROM DOCUMENT:
        {context}

        USER QUESTION:
        {question}

        FORMATTING INSTRUCTIONS:
        1. Use **Markdown** for clarity.
        2. Use ## for section headings if the answer is long.
        3. Use bullet points for lists.
        4. Use **bold text** for key terms.
        5. If the answer is not in context, say: "I'm sorry, but the document does not contain information regarding [topic]."
        6. Tone: Professional and concise.
    """
    
    try:
        # Get the model instance lazily
        model = get_chat_model()
        
        # Use async call for content generation
        response = await model.generate_content_async(prompt)
        return {
            "answer": response.text if response.text else "The AI could not generate a response. Please try rephrasing."
        }
    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str:
            raise HTTPException(status_code=429, detail="AI quota exceeded. Please wait a moment.")
        print(f"❌ AI Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation Error: {e}")
