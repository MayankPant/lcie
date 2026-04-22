from pathlib import Path

EXTENSIONS = [".py", ".js", ".ts", ".go", ".rs", ".jave"]

def scan_repo(path):
    files  = []
    for p in Path(path).rglob("*"):
        if p.suffix in EXTENSIONS:
            files.append(p)
            
    return files
