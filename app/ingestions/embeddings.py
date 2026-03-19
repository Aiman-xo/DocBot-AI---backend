import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)


# this creates the vector data for the chunks of texts we extract from the pdf
def create_embeddings(chunks):
    if not chunks:
        return []

    # Using batch embedding for much faster performance
    # This prevents the "502 Bad Gateway" timeout by making 1 API call instead of dozens
    response = genai.embed_content(
        model="models/gemini-embedding-001",
        content=chunks,
        task_type="retrieval_document"
    )

    embeddings = []
    # If a single chunk was passed as a string, wrap it in a list to handle it consistently
    if isinstance(chunks, str):
        embeddings.append({
            "text": chunks,
            "embedding": response['embedding']
        })
    else:
        # response['embedding'] will be a list of embedding vectors
        for text, emb in zip(chunks, response['embedding']):
            embeddings.append({
                "text": text,
                "embedding": emb
            })

    return embeddings