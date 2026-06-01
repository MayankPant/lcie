from .scanner import scan_repo
from .chunker import chunk_file

def index_repo(path:str):
    files = scan_repo(path)
    
    for filepath in files:
        chunks = chunk_file(filepath=filepath)
        
        for chunk in chunks:
            print(chunk[:100])
