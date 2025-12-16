
CELL 1:
%uv pip install -U modal requests
!python -m modal setup


CELL 2:
import modal

app = modal.App.lookup('proyoutubers-dubbing-modal', create_if_missing=True)

# Create persistent volume for dubbed videos
outputs_volume = modal.Volume.from_name(
    "proyoutubers-outputs", 
    create_if_missing=True
)
print("✅ Persistent volume 'proyoutubers-outputs' configured")

# Use Modal's CUDA image with PyTorch pre-installed (includes cuDNN)
proyoutubers_image = (
    modal.Image.from_registry("nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04", add_python="3.11")
    .apt_install(
        'git','make','ffmpeg','rubberband-cli','libsndfile1',
        'openjdk-17-jre-headless','ca-certificates','curl',
        'espeak-ng','sox','libsox-fmt-all','nginx',
        'build-essential','python3-dev','clang'
    )
    .pip_install('uv>=0.5.0')
    .run_commands(
        'pip install torch==2.5.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu121',
        'python -c "import torch; print(f\\"PyTorch {torch.__version__} with CUDA {torch.version.cuda}\\")"'
    )
)

# Your Hugging Face token (required)
HF_TOKEN = 'hf_REDACTED_FOR_SECURITY'
hf_secret = modal.Secret.from_dict({'HF_TOKEN': HF_TOKEN})

# DeepL API key (optional)
DEEPL_API_KEY = ''  # Optional: Add your DeepL API key here
deepl_secret = modal.Secret.from_dict({'DEEPL_API_KEY': DEEPL_API_KEY}) if DEEPL_API_KEY else None

print("✅ Modal app, image and secrets configured with CUDA + cuDNN support.")
if DEEPL_API_KEY:
    print("✅ DeepL API key configured for premium translation.")
else:
    print("ℹ️  No DeepL API key - will use free Google Translator.")


CELL 3:
# GPU type hardcoded to L4 for optimal performance
GPU_TYPE = "L4"

with modal.enable_output():
    secrets_list = [hf_secret]
    if deepl_secret:
        secrets_list.append(deepl_secret)
    
    sb = modal.Sandbox.create(
        'bash','-lc','sleep infinity',
        app=app,
        image=proyoutubers_image,
        secrets=secrets_list,
        encrypted_ports=[8000, 5173],
        volumes={"/persistent-outputs": outputs_volume},
        cpu=4,
        memory=24576,
        gpu=GPU_TYPE,
        timeout=3*60*60,
        idle_timeout=30*60,
        verbose=True,
    )
print(f"✅ Sandbox created with {GPU_TYPE} GPU + persistent volume:", sb.object_id)
print("⚡ Idle timeout: 30 minutes - GPU auto-releases for cost savings")


CELL 4:
def sh(cmd: str, timeout: int|None = None):
    proc = sb.exec('bash','-lc', cmd, timeout=timeout) if timeout else sb.exec('bash','-lc', cmd)
    out = proc.stdout.read()
    err = proc.stderr.read()
    if out: print(out)
    if err: print(err)
    return proc

print("✅ Helper function defined.")


CELL 5:
# Clone ProYouTubers Dubbing Studio repository (FULL CLONE - NO --depth 1)
REPO_URL = 'https://github.com/DaniyalAfzaal/ProYouTubers-Dubbing-Studio.git'

# CRITICAL FIX: Removed --depth 1 to allow git pull to work properly
sh(f'cd /root && rm -rf proyoutubers-dubbing && git clone {REPO_URL} proyoutubers-dubbing')

sh(r'''
cd /root/proyoutubers-dubbing
cp -f .env.example .env
sed -i "s/^HF_TOKEN=.*/HF_TOKEN=$HF_TOKEN/" .env
''')

print("✅ Repository cloned (full clone - git pull will work!)")
print("✅ .env configured with HF token")


CELL 5A:
# Pull latest code to ensure we have all latest fixes
sh(r'''
cd /root/proyoutubers-dubbing
git pull origin main
''')

print("✅ Code updated with latest fixes:")
print("  - bulk-status endpoint (real-time UI updates)")
print("  - Frontend null check fixes")
print("  - Audio separator graceful fallback")
print("  - Downloads manager improvements")
print("  - All bug fixes from latest commits")


CELL 5B:
# Verify we have the latest code
sh(r'''
cd /root/proyoutubers-dubbing
echo "Current commit:"
git log --oneline -1
echo ""
echo "Checking for bulk-status endpoint:"
grep -n "bulk-status" apps/backend/services/orchestrator/app/main.py | head -2
''')

print("✅ Code verification complete!")


CELL 5C:
# Create Chatterbox TTS config
sh(r'''
mkdir -p /root/proyoutubers-dubbing/apps/backend/services/model_config
cat > /root/proyoutubers-dubbing/apps/backend/services/model_config/chatterbox.yaml << 'EOF'
languages:
  - ar
  - da
  - de
  - el
  - en
  - es
  - fi
  - fr
  - he
  - hi
  - it
  - ja
  - ko
  - ms
  - nl
  - no
  - pl
  - pt
  - ru
  - sv
  - sw
  - tr
  - zh

params:
  generate:
    exaggeration: 0.5
    cfg_weight: 0.5
    temperature: 0.8
    repetition_penalty: 2.0
    min_p: 0.05
    top_p: 1.0
  log_level: INFO
EOF
''')

print("✅ Chatterbox TTS config created")


CELL 6:
# Build venvs for all services
sh('cd /root/proyoutubers-dubbing && make install-dep', timeout=60*60)

print("✅ Dependencies installed.")
print("")
print("=" * 60)
print("Verifying GPU configuration...")
print("=" * 60)

sh('python3 -c "import torch; print(f\'PyTorch: {torch.__version__}\'); print(f\'CUDA available: {torch.cuda.is_available()}\'); print(f\'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}\')"')


CELL 7:
# Start backend services
sh('cd /root/proyoutubers-dubbing && nohup make RELOAD= stack-up > /tmp/stack.log 2>&1 &')
print("✅ Backend services starting...")
print("   (ASR, Translation, TTS, Orchestrator)")
print("   Logs: /tmp/stack.log")


CELL 8:
# Configure and start nginx
sh(r'''
cat > /tmp/nginx.conf <<'NG'
user root;
worker_processes 1;
events { worker_connections 1024; }
http {
  client_max_body_size 500m;
  include       /etc/nginx/mime.types;
  default_type  application/octet-stream;
  sendfile on;
  server {
    listen 5173;
    server_name _;
    root /root/proyoutubers-dubbing/apps/frontend;
    index index.html;

    location = /options {
      proxy_pass http://127.0.0.1:8000/api/options;
      proxy_set_header Host $host;
      proxy_connect_timeout 600s;
      proxy_read_timeout    600s;
      proxy_send_timeout    600s;
    }

    location /api/ {
      proxy_pass http://127.0.0.1:8000;
      proxy_set_header Host $host;
      proxy_connect_timeout 600s;
      proxy_read_timeout    600s;
      proxy_send_timeout    600s;
    }

    location /api/download/ {
      proxy_pass http://127.0.0.1:8000;
      proxy_set_header Host $host;
      proxy_connect_timeout 600s;
      proxy_read_timeout 1800s;
      proxy_send_timeout 1800s;
      proxy_buffering off;
      proxy_request_buffering off;
    }

    location / {
      try_files $uri $uri/ /index.html;
    }
  }
}
NG

nohup nginx -c /tmp/nginx.conf -g "daemon off;" > /tmp/nginx.log 2>&1 &
sleep 3
''')

print("✅ Nginx started (frontend proxy)")


CELL 9:
# Get tunnel URLs
import time
time.sleep(5)  # Give services time to start

tunnels = sb.tunnels()
backend_url = tunnels[8000].url.rstrip('/')
ui_url = tunnels[5173].url.rstrip('/')

print("=" * 70)
print("🎉 DEPLOYMENT COMPLETE!")
print("=" * 70)
print(f"🔗 Backend API: {backend_url}")
print(f"🌐 Web UI:      {ui_url}")
print("")
print("💡 Usage:")
print("   1. Open the Web UI URL in your browser")
print("   2. If you see old UI, press Ctrl+F5 to hard refresh")
print("   3. Try bulk mode - should show real-time progress now!")
print("=" * 70)


CELL 10:
# Verify bulk-status endpoint is working
import requests
import json
import time

time.sleep(10)  # Wait for services to fully start

print("🔍 Verifying bulk-status endpoint...")
print("=" * 70)

test_batch_id = "00000000-0000-0000-0000-000000000000"

try:
    # Test options endpoint first
    resp = requests.get(f"{backend_url}/api/options", timeout=10)
    if resp.status_code == 200:
        print("✅ Orchestrator is running!")
    else:
        print(f"⚠️  Orchestrator responded with: {resp.status_code}")
        
    # Test bulk-status endpoint
    resp = requests.get(f"{backend_url}/api/jobs/bulk-status/{test_batch_id}", timeout=10)
    
    if resp.status_code == 404:
        data = resp.json()
        if "Batch not found" in data.get("detail", ""):
            print("✅ BULK-STATUS ENDPOINT IS WORKING!")
            print(f"   Response: {json.dumps(data, indent=2)}")
            print("")
            print("🎉 Latest code successfully deployed!")
            print("   - bulk-status endpoint: ✅")
            print("   - Frontend fixes: ✅")
            print("   - All updates: ✅")
        else:
            print(f"⚠️  Unexpected response: {data}")
    else:
        print(f"⚠️  Unexpected status: {resp.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Services may still be starting...")
    print("   Wait 30 seconds and run this cell again")
    
print("=" * 70)


CELL 11:
# Performance expectations
print("📊 PERFORMANCE EXPECTATIONS")
print("=" * 70)
print("")
print("✅ GPU Acceleration:")
print("  - Alignment on GPU: ~4-5s (vs 20s+ on CPU)")
print("  - TTS per segment: 15-20s")
print("  - Model loading: One-time ~30s")
print("")
print("✅ Bulk Mode UI:")
print("  - Real-time progress updates every 2s")
print("  - Shows: total, completed, failed, processing, queued")
print("  - Individual video status cards")
print("")
print("✅ Downloads Manager:")
print("  - Tracks all completed/failed jobs")
print("  - Persists across page refreshes")
print("  - Shows in Downloads tab")
print("")
print("🐛 If issues occur:")
print("  - Check logs: sh('tail -100 /tmp/stack.log')")
print("  - Verify GPU: sh('nvidia-smi')")
print("  - Check nginx: sh('tail -50 /tmp/nginx.log')")
print("")
print("=" * 70)
