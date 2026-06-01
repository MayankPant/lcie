from sentence_transformers import SentenceTransformer
from numpy.typing import NDArray
import numpy as np
from numpy.typing import NDArray
from lcie import config

model = SentenceTransformer(config.EMBED_MODEL)


def embed_chunks(chunks: list[str]) -> NDArray[np.float32]:
    return model.encode( #type: ignore
        chunks,
        convert_to_numpy=True
    )
