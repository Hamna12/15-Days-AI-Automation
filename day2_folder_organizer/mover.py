import shutil
import os
from pathlib import Path

def move_file(source_path, target_folder):
    """
    Moves a file to a specific target folder. Creates the folder if it doesn't exist.
    """
    try:
        source = Path(source_path)
        if not source.exists():
            return False, f"Source file does not exist: {source_path}"
        
        dest_dir = source.parent / target_folder
        
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            
        dest_path = dest_dir / source.name
        
        # Avoid overwriting
        if dest_path.exists():
            dest_path = dest_dir / f"copy_{source.name}"
            
        shutil.move(str(source), str(dest_path))
        return True, str(dest_path)
    except Exception as e:
        return False, str(e)
