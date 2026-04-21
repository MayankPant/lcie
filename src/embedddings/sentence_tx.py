from sentence_transformers import SentenceTransform

model = SentenceTransform("all-MiniLM-L6-v2")

def embed_chunks(chunks):
    return model.encode(chunks)
