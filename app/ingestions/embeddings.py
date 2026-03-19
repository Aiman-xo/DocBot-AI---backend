import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)


# this creates the vector data for the chunks of texts we extract from the pdf
def create_embeddings(chunks):
    if not chunks:
        return []

    # If it's a single string, handle it separately
    if isinstance(chunks, str):
        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=chunks,
            task_type="retrieval_document"
        )
        return [{"text": chunks, "embedding": response['embedding']}]

    # Batching to stay within Gemini API limits (usually ~100 items per call)
    batch_size = 90  # Safe limit
    embeddings = []

    for i in range(0, len(chunks), batch_size):
        current_batch = chunks[i : i + batch_size]
        
        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=current_batch,
            task_type="retrieval_document"
        )

        for text, emb in zip(current_batch, response['embedding']):
            embeddings.append({
                "text": text,
                "embedding": emb
            })

    return embeddings