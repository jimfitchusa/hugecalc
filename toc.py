import time
import os
import tempfile

toc_time = time.time()
temp_path = os.path.join(tempfile.gettempdir(), 'tic_timestamp.tmp')

try:
    with open(temp_path, 'r') as f:
        tic_time = float(f.read().strip())
    os.remove(temp_path)
    print(f"\nElapsed: {toc_time - tic_time:.3f}s")
except FileNotFoundError:
    print("\nElapsed: Error (tic.py was not run first)")
