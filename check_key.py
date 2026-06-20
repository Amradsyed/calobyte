import os
from pathlib import Path

for line in Path('.env').read_text().splitlines():
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k.strip()] = v.strip()

key = os.getenv('NVIDIA_API_KEY')
print('Key found:', repr(key))