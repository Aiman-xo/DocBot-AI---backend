from app.models.document_model import DocumentModel
from app.vectorstore.chromadb_client import collection
from app.ingestions.embeddings import create_embeddings
from app.core.config import settings
from fastapi import HTTPException
import google.generativeai as genai

genai.configure(api_key=settings.GEMINI_API_KEY)

def ask_question(request,db,user):
    question = request.question
    document_id = request.document_id

    doc = db.query(DocumentModel).filter(
        DocumentModel.id == document_id, 
        DocumentModel.user_id == user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    # Get question embedding
    # this sends the data according to the function create_embeddings 
    # it accepts the things in list format beacuse it was originally assigned to accept all the chunks of text from the pdf
    # to store to the db but now we only giving a single question to that so we write like  [question]
    # and from that we extract the ["embeddings"] were the vector data lies
    # after this step we get the vector data for the asked question
    question_embedding_data = create_embeddings([question])
    requested_question_embedding = question_embedding_data[0]["embedding"]

    # now we have to query through the vector_db collections to find the match
    results= collection.query(
        query_embeddings=[requested_question_embedding],
        # finds the closest 5 vector datas
        n_results=5,
        # security check cannot access other users pdf of the same
        where={
            "$and": [
                {"user_id": user.id},
                {"document_id": document_id}
            ]
        }
    )

    # extracts the text 
    chunks = results["documents"][0]
    # joins all of the to create a string
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
        3. Use bullet points for lists of features, skills, or facts.
        4. Use **bold text** for key terms or names.
        5. If the answer is not in the context, say: "I'm sorry, but the document does not contain information regarding [topic]."
        6. Keep the tone professional and concise.
        """
    
    model = genai.GenerativeModel(model_name ="gemini-3.1-flash-lite-preview",
        system_instruction="You are a specialized document analyzer. You always respond with structured Markdown," \
        " using headers and bullet points. Never mention 'Based on the provided context'—just provide the answer directly and professionally."
        
        ) # gemini-1.5-flash-latest 👍
    
    try:
        response = model.generate_content(prompt)
    except Exception as e:
        # Check if it's a rate limit exception (often ResourceExhausted, but it could be wrapped)
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str or "exhausted" in error_str:
            raise HTTPException(status_code=429, detail="Per minute request limit exceeded. Please wait 60 seconds before trying again.")
        raise HTTPException(status_code=500, detail=f"An error occurred while communicating with the AI model: {e}")

    return {
        "answer": response.text if response.text else "The AI could not generate a response. Please try rephrasing your question."
    }
