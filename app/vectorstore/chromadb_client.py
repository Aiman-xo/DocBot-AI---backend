import chromadb

_client = None
_collection = None

# LAZY LOADING CHROMADB
# Prevents ChromaDB from indexing its large SQLite/hnswlib files immediately at server boot
# which causes the 2-minute timeout on 512MB RAM servers.
def get_chroma_collection():
    global _client, _collection
    if _client is None:
        _client = chromadb.PersistentClient(path="chroma_db")
        _collection = _client.get_or_create_collection(name="pdf_documents")
    return _collection


def store_embeddings(embeddings, user_id, document_id):
    col = get_chroma_collection()
    ids = []
    vectors = []
    documents = []
    metadatas = []

    for i, item in enumerate(embeddings):
        ids.append(f"{user_id}_{document_id}_{i}") # created small ids for each chunks
        vectors.append(item["embedding"]) # actual vector data of a chunk
        documents.append(item["text"]) 
        metadatas.append({
            "user_id": user_id,
            "document_id": document_id
        })

    col.add(
        ids=ids,
        embeddings=vectors,
        documents=documents,
        metadatas=metadatas
    )

def query_embeddings(query_embeddings, n_results, where):
    col = get_chroma_collection()
    return col.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        where=where
    )