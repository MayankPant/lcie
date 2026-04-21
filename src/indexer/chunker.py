def chunk_file(path, chunk_size=40):
    with open(path, "r", errors="ignore") as f:
        lines = f.readlines()
        
        chunks = []
        
        for i in range(0, len(lines), chunk_size):
            chunk = "".join(lines[i: i + chunk_size])
            chunks.append(chunk)
            
        return chunks
