# utils/file_ops.py

import os
import shutil

def copy_with_dedup(src: str, dst_dir: str, filename: str):
    base, ext = os.path.splitext(filename)
    dst = os.path.join(dst_dir, filename)

    counter = 1
    while os.path.exists(dst):
        dst = os.path.join(dst_dir, f"{base}_{counter}{ext}")
        counter += 1

    shutil.copy(src, dst)
