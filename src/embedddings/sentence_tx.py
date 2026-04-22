from sentence_transformers import SentenceTransform
from lcie.config import EMBED_MODEL

model = SentenceTransform(EMBED_MODEL)

def embed_chunks(chunks):
    return model.encode(chunks)
