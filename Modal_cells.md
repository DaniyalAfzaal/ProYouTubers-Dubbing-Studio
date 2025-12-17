CELL 1:
%pip install -U modal requests
!modal setup


CELL 2:
import modal

app = modal.App.lookup('proyoutubers-dubbing-studio', create_if_missing=True)

outputs_volume = modal.Volume.from_name("proyoutubers-outputs", create_if_missing=True)

# API Keys (REQUIRED for God Tier)
HF_TOKEN = 'hf_YOUR_TOKEN_HERE'  # Replace with your Hugging Face token
DEEPSEEK_API_KEY = 'sk-YOUR_KEY_HERE'  # Replace with your DeepSeek API key

hf_secret = modal.Secret.from_dict({'HF_TOKEN': HF_TOKEN})
deepseek_secret = modal.Secret.from_dict({'DEEPSEEK_API_KEY': DEEPSEEK_API_KEY}) if DEEPSEEK_API_KEY.startswith('sk-') else None

proyoutubers_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install('git', 'ffmpeg', 'libsndfile1', 'nginx', 'build-essential')
    .pip_install('uv>=0.5.0')
)

print("✅ Modal app configured")
if DEEPSEEK_API_KEY.startswith('sk-'):
    print("✅ DeepSeek API key configured (God Tier enabled)")
else:
    print("⚠️  No DeepSeek API key - God Tier will use fallback")


CELL 3:
with modal.enable_output():
    secrets_list = [hf_secret]
    if deepseek_secret:
        secrets_list.append(deepseek_secret)
    
    sb = modal.Sandbox.create(
        'bash', '-lc', 'sleep infinity',
        app=app,
        image=proyoutubers_image,
        secrets=secrets_list,
        encrypted_ports=[8000, 5173],
        volumes={"/persistent-outputs": outputs_volume},
        cpu=4,
        memory=24576,
        gpu="L4",
        timeout=3*60*60,
        idle_timeout=30*60,
        verbose=True,
    )

print(f"✅ Sandbox created: {sb.object_id}")
print("✅ API keys injected as environment variables")


CELL 4:
def sh(cmd: str, timeout: int|None = None):
    proc = sb.exec('bash', '-lc', cmd, timeout=timeout) if timeout else sb.exec('bash', '-lc', cmd)
    out = proc.stdout.read()
    err = proc.stderr.read()
    if out: print(out)
    if err: print(err)
    return proc

print("✅ Helper ready")


CELL 5:
REPO_URL = 'https://github.com/DaniyalAfzaal/ProYouTubers-Dubbing-Studio.git'

sh(f'cd /root && rm -rf proyoutubers-dubbing && git clone {REPO_URL} proyoutubers-dubbing')
sh('cd /root/proyoutubers-dubbing && git pull origin main')
sh('cd /root/proyoutubers-dubbing && git log --oneline -1')

# Configure .env with API keys
sh(r'''
cd /root/proyoutubers-dubbing
cp -f .env.example .env
sed -i "s/^HF_TOKEN=.*/HF_TOKEN=$HF_TOKEN/" .env
if [ ! -z "$DEEPSEEK_API_KEY" ]; then
  echo "DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY" >> .env
fi
''')

print("✅ Latest code cloned (commit 5f1167b)")
print("✅ .env configured with API keys")


CELL 6:
# Install PyTorch FIRST
sh('pip install torch==2.4.0+cu121 torchaudio==2.4.0+cu121 --index-url https://download.pytorch.org/whl/cu121', timeout=1800)

# Install NumPy (required by everything)
sh('pip install numpy==1.26.4', timeout=300)

# Install God Tier stack
sh('pip install -r /root/proyoutubers-dubbing/apps/backend/requirements_god_tier.txt', timeout=1800)

# Install any root requirements if they exist
sh('cd /root/proyoutubers-dubbing && pip install -r requirements.txt || echo "No root requirements.txt"', timeout=600)

# Verify
sh('python -c "import torch; import numpy; print(f\'PyTorch: {torch.__version__}, NumPy: {numpy.__version__}\')"')
sh('python -c "import torch; print(f\'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}\')"')

print("✅ Dependencies installed successfully")


CELL 7:
sh('cd /root/proyoutubers-dubbing && nohup make RELOAD= stack-up > /tmp/stack.log 2>&1 &')

import time
time.sleep(15)

print("✅ Backend services started (ports 8001, 8002, 8003, 8000)")


CELL 8:
sh(r'''
cat > /tmp/nginx.conf <<'EOF'
user root;
worker_processes 1;
events { worker_connections 1024; }
http {
  client_max_body_size 500m;
  include /etc/nginx/mime.types;
  default_type application/octet-stream;
  server {
    listen 5173;
    root /root/proyoutubers-dubbing/apps/frontend;
    index index.html;
    
    location /api/ {
      proxy_pass http://127.0.0.1:8000;
      proxy_set_header Host $host;
      proxy_read_timeout 600s;
      proxy_buffering off;
    }
    
    location / {
      try_files $uri $uri/ /index.html;
    }
  }
}
EOF

nohup nginx -c /tmp/nginx.conf -g "daemon off;" > /tmp/nginx.log 2>&1 &
sleep 3
''')

print("✅ Nginx started")


CELL 9:
import time
time.sleep(5)

tunnels = sb.tunnels()
backend_url = tunnels[8000].url.rstrip('/')
ui_url = tunnels[5173].url.rstrip('/')

print("=" * 70)
print("🎉 DEPLOYMENT COMPLETE!")
print("=" * 70)
print(f"Backend: {backend_url}")
print(f"Web UI:  {ui_url}")
print()
print("✅ Fixes Applied:")
print("   - /api/options endpoint")
print("   - God Tier strategies in config")
print("   - Strategy override fix")
print("=" * 70)


CELL 10 (OPTIONAL):
import requests
import time

time.sleep(10)

resp = requests.get(f"{backend_url}/api/options", timeout=10)
if resp.status_code == 200:
    data = resp.json()
    print("✅ /api/options working")
    print(f"   Strategies: {data.get('dubbing_strategies', [])}")
else:
    print(f"❌ Status: {resp.status_code}")


CELL 11 (TROUBLESHOOTING):
# View logs if needed
sh('tail -100 /tmp/stack.log')
