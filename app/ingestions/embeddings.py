import httpx
import asyncio
from app.core.config import settings

# LIGHTWEIGHT REST API INGESTION
# Instead of importing the heavy 'google-generativeai' SDK (which uses 100MB+ RAM),
# we call the Gemini API directly via HTTPX to stay under Render's 512MB limit.

async def create_embeddings_rest(chunks):
    """Create embeddings for PDF chunks using Gemini REST API (Low memory)"""
    if not chunks:
        return []

    # If it's a single string, handle it
    is_single = isinstance(chunks, str)
    chunk_list = [chunks] if is_single else chunks
    
    # Gemini allows batch embedding of up to 100 per request
    batch_size = 90
    semaphore = asyncio.Semaphore(3)  # Reduce concurrency to save RAM on 512MB limit , allows 3 batch per request after 1 batch finishes
    # others can start sending the embedding request to google.
    
    batches = [chunk_list[i : i + batch_size] for i in range(0, len(chunk_list), batch_size)]
    
    async def process_batch(current_batch):
        # Using v1beta for embedding batches
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={settings.GEMINI_API_KEY}"
        
        requests = []
        for text in current_batch:
            requests.append({
                "model": "models/gemini-embedding-001",
                "content": {"parts": [{"text": text}]},
                "task_type": "RETRIEVAL_DOCUMENT"
            })
            
        payload = {"requests": requests}
        
        async with semaphore:
            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    # extract embeddings from the batch response
                    return list(zip(current_batch, [emb["values"] for emb in data["embeddings"]]))
                except Exception as e:
                    return []

    # Run batches in parallel, but limited by the semaphore to save memory
    results = await asyncio.gather(*(process_batch(b) for b in batches))
    
    all_embeddings = []
    for batch_result in results:
        for text, emb in batch_result:
            all_embeddings.append({
                "text": text,
                "embedding": emb
            })

    return all_embeddings

# Map the old create_embeddings to the new REST version for compatibility
async def create_embeddings(chunks):
    return await create_embeddings_rest(chunks)