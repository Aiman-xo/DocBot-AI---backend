# creating the chunks from the big text without losing the context

def creating_chunks(text,chunk_size = 500,over_lap=50):

    chunks = []

    for i in range(0,len(text),chunk_size-over_lap):
        chunk = text[i:i+chunk_size]
        chunks.append(chunk)
    
    return chunks