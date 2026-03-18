import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)


# this creates the vector data for the chunks of texts we extract from the pdf
def create_embeddings(chunks):

    embeddings = []

    for chunk in chunks:

        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=chunk
        )

        embeddings.append({
            "text": chunk,
            "embedding": response["embedding"]
        })

    return embeddings