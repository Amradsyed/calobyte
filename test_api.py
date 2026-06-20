import os, json, urllib.request, urllib.error
from pathlib import Path

for line in Path('.env').read_text().splitlines():
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k.strip()] = v.strip()

key = os.getenv('NVIDIA_API_KEY')
print('Testing key:', key[:15] + '...')

payload = json.dumps({
    "model": "moonshotai/kimi-k2.6",
    "messages": [{"role": "user", "content": "Say hi in one word."}],
    "max_tokens": 10
}).encode()

req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=payload,
    headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
        print("SUCCESS:", data["choices"][0]["message"]["content"])
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"FAILED {e.code} {e.reason}")
    print("Details:", body)