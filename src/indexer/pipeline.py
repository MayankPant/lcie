from .scanner import scan_repo
from .chunker import chunk_file

def index_repo(path):
    files = scan_repo(path)
    
    for file in files:
        chunks = chunk_file(file)
        
        for chunk in chunks:
            print(chunk[:100])
