import chromadb

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_or_create_collection(
    name="pdf_documents"
)


def store_embeddings(embeddings, user_id, document_id):

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

    collection.add(
        ids=ids,
        embeddings=vectors,
        documents=documents,
        metadatas=metadatas
    )