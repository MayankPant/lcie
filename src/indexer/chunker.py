from lcie.config import CHUNK_SIZE
from pathlib import Path
def chunk_file(filepath: Path, chunk_size: int=CHUNK_SIZE) -> list[str]:
    with open(filepath, "r", errors="ignore") as f:
        lines = f.readlines()
        
        chunks: list[str] = []
        
        for i in range(0, len(lines), chunk_size):
            chunk = "".join(lines[i: i + chunk_size])
            chunks.append(chunk)
            
        return chunks
