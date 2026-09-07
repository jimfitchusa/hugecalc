import time
import os
import tempfile

temp_path = os.path.join(tempfile.gettempdir(), 'tic_timestamp.tmp')
with open(temp_path, 'w') as f:
    f.write(str(time.time()))
