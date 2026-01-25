import os
from pathlib import Path

def scan_directory(directory_path):
    """
    Scans the given directory and returns a list of files with their metadata.
    """
    files = []
    path = Path(directory_path)
    
    if not path.is_dir():
        return None
        
    for item in path.iterdir():
        if item.is_file():
            stats = item.stat()
            files.append({
                "name": item.name,
                "extension": item.suffix.lower(),
                "size_kb": round(stats.st_size / 1024, 2),
                "path": str(item.absolute())
            })
    return files
