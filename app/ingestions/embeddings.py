import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)


import asyncio

# this creates the vector data for the chunks of texts we extract from the pdf
async def create_embeddings(chunks):
    if not chunks:
        return []

    # If it's a single string, handle it
    if isinstance(chunks, str):
        response = await genai.embed_content_async(
            model="models/text-embedding-004",
            content=chunks,
            task_type="retrieval_document"
        )
        return [{"text": chunks, "embedding": response['embedding']}]

    batch_size = 90  # Gemini safe limit
    semaphore = asyncio.Semaphore(5)  # Limit concurrency to 5 parallel requests
    
    batches = [chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)]
    
    async def process_batch(current_batch):
        async with semaphore:
            try:
                response = await genai.embed_content_async(
                    model="models/text-embedding-004",
                    content=current_batch,
                    task_type="retrieval_document"
                )
                return list(zip(current_batch, response['embedding']))
            except Exception as e:
                print(f"❌ Error in embedding batch: {e}")
                return []

    # Run batches in parallel, but limited by the semaphore! 🚦 
    results = await asyncio.gather(*(process_batch(b) for b in batches))
    
    embeddings = []
    for batch_result in results:
        for text, emb in batch_result:
            embeddings.append({
                "text": text,
                "embedding": emb
            })

    return embeddings