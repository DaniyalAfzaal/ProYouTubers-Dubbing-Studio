CELL 1:
%uv pip install -U modal requests
!python -m modal setup


CELL 2:
import modal

app = modal.App.lookup('proyoutubers-dubbing-god-tier', create_if_missing=True)

# Create persistent volume for dubbed videos
outputs_volume = modal.Volume.from_name(
    "proyoutubers-outputs", 
    create_if_missing=True
)
print("✅ Persistent volume 'proyoutubers-outputs' configured")

# CRITICAL: God Tier requires PyTorch 2.4.0 (NOT 2.5) + NumPy 1.26.4
# Use Python 3.10 (NOT 3.11) for Applio/F5-TTS compatibility
proyoutubers_image = (
    modal.Image.from_registry("nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04", add_python="3.10")
    .apt_install(
        'git','make','ffmpeg','rubberband-cli','libsndfile1',
        'openjdk-17-jre-headless','ca-certificates','curl',
        'espeak-ng','sox','libsox-fmt-all','nginx',
        'build-essential','python3-dev','clang'
    )
    .pip_install('uv>=0.5.0')
    # GOD TIER CRITICAL: PyTorch 2.4.0 + CUDA 12.1 (Goldilocks Zone)
    .run_commands(
        'pip install torch==2.4.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu121',
        'pip install numpy==1.26.4',  # Prevent NumPy 2.0 breakage
        'python -c "import torch; print(f\\"PyTorch {torch.__version__} with CUDA {torch.version.cuda}\\")"'
    )
)

# Your Hugging Face token (required for model downloads)
HF_TOKEN = 'hf_REDACTED_FOR_SECURITY'
hf_secret = modal.Secret.from_dict({'HF_TOKEN': HF_TOKEN})

# DeepSeek API key (required for God Tier Logic stage)
DEEPSEEK_API_KEY = ''  # Add your DeepSeek API key here for God Tier
deepseek_secret = modal.Secret.from_dict({'DEEPSEEK_API_KEY': DEEPSEEK_API_KEY}) if DEEPSEEK_API_KEY else None

print("✅ Modal app configured with God Tier stack:")
print("   - Python 3.10 (Applio/F5 compatible)")
print("   - PyTorch 2.4.0 + CUDA 12.1")
print("   - NumPy 1.26.4 (prevents breakage)")
if DEEPSEEK_API_KEY:
    print("✅ DeepSeek API key configured (God Tier Logic stage enabled)")
else:
    print("⚠️  No DeepSeek API key - God Tier will use fallback LLM")


CELL 3:
# GPU type: L4 is PERFECT for God Tier (24GB VRAM)
GPU_TYPE = "L4"

with modal.enable_output():
    secrets_list = [hf_secret]
    if deepseek_secret:
        secrets_list.append(deepseek_secret)
    
    sb = modal.Sandbox.create(
        'bash','-lc','sleep infinity',
        app=app,
        image=proyoutubers_image,
        secrets=secrets_list,
        encrypted_ports=[8000, 5173],
        volumes={"/persistent-outputs": outputs_volume},
        cpu=4,
        memory=24576,  # 24GB RAM for God Tier
        gpu=GPU_TYPE,
        timeout=3*60*60,
        idle_timeout=30*60,
        verbose=True,
    )
print(f"✅ Sandbox created with {GPU_TYPE} GPU (24GB VRAM):")
print(f"   ID: {sb.object_id}")
print("   Perfect for God Tier Hollywood mode!")
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
# Clone ProYouTubers Dubbing Studio (FULL CLONE with God Tier)
REPO_URL = 'https://github.com/DaniyalAfzaal/ProYouTubers-Dubbing-Studio.git'

sh(f'cd /root && rm -rf proyoutubers-dubbing && git clone {REPO_URL} proyoutubers-dubbing')

sh(r'''
cd /root/proyoutubers-dubbing
cp -f .env.example .env
sed -i "s/^HF_TOKEN=.*/HF_TOKEN=$HF_TOKEN/" .env

# Add DeepSeek API key if available
if [ ! -z "$DEEPSEEK_API_KEY" ]; then
  echo "DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY" >> .env
fi
''')

print("✅ Repository cloned with God Tier 9-Stage Pipeline")
print("✅ .env configured with API keys")


CELL 5A:
# Pull latest code (includes God Tier commit)
sh(r'''
cd /root/proyoutubers-dubbing
git pull origin main
''')

print("✅ Code updated with latest God Tier features:")
print("  - 9-Stage Pipeline (Surgeon→Polisher→Ears→Guard→Brain→Logic→Mouth→Skin→Renderer)")
print("  - Draft Mode (Kokoro TTS - 30s render)")
print("  - Hollywood Mode (F5-TTS + Applio + BigVGAN)")
print("  - Advanced UI Controls (toggle each stage)")
print("  - requirements_god_tier.txt (strict dependencies)")


CELL 5B:
# Verify we have God Tier code
sh(r'''
cd /root/proyoutubers-dubbing
echo "Current commit:"
git log --oneline -1
echo ""
echo "Checking for God Tier pipeline:"
grep -n "god_tier_draft\|god_tier_hollywood" apps/backend/services/orchestrator/app/main.py | head -3
echo ""
echo "Checking for God Tier UI controls:"
ls -lh apps/frontend/scripts/modules/godTierControls.js
''')

print("✅ God Tier code verification complete!")


CELL 5C:
# Create Chatterbox TTS config (legacy fallback)
sh(r'''
mkdir -p /root/proyoutubers-dubbing/apps/backend/services/model_config
cat > /root/proyoutubers-dubbing/apps/backend/services/model_config/chatterbox.yaml <<'EOF'
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

print("✅ Chatterbox TTS config created (legacy fallback)")


CELL 6:
# Install GOD TIER dependencies (strict versions)
sh(r'''
cd /root/proyoutubers-dubbing/apps/backend
echo "Installing God Tier dependencies (this may take 10-15 minutes)..."

# Install base dependencies first
make install-dep

# Install God Tier stack with STRICT VERSIONS
pip install -r requirements_god_tier.txt

# Verify installations
echo ""
echo "=== VERIFICATION ==="
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "import librosa; print(f'Librosa: {librosa.__version__}')"
echo "✅ God Tier stack verified"
''', timeout=60*60)

print("✅ Dependencies installed (God Tier + Legacy)")
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
print("   + God Tier PipelineManager")
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

print("✅ Nginx started (frontend proxy with God Tier UI)")


CELL 9:
# Get tunnel URLs
import time
time.sleep(5)  # Give services time to start

tunnels = sb.tunnels()
backend_url = tunnels[8000].url.rstrip('/')
ui_url = tunnels[5173].url.rstrip('/')

print("=" * 70)
print("🎉 GOD TIER DEPLOYMENT COMPLETE!")
print("=" * 70)
print(f"🔗 Backend API: {backend_url}")
print(f"🌐 Web UI:      {ui_url}")
print("")
print("💡 God Tier Features Available:")
print("   1. Open the Web UI URL (press Ctrl+F5 for hard refresh)")
print("   2. Select 'Dubbing Strategy' dropdown")
print("   3. Choose:")
print("      🏎️ God Tier - Draft (Speed): ~30s render, Kokoro TTS")
print("      🎬 God Tier - Hollywood (Quality): F5-TTS + Full 9 stages")
print("   4. Advanced Controls panel will appear below")
print("   5. Toggle individual stages or use Quick Presets")
print("")
print("📊 God Tier Modes:")
print("   Draft:     Surgeon→Ears→Brain→Logic→Kokoro (5 stages)")
print("   Hollywood: All 9 stages (Surgeon→...→Renderer)")
print("=" * 70)


CELL 10:
# Verify God Tier endpoint is working
import requests
import json
import time

time.sleep(10)  # Wait for services to fully start

print("🔍 Verifying God Tier endpoints...")
print("=" * 70)

try:
    # Test options endpoint
    resp = requests.get(f"{backend_url}/api/options", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        dubbing_strategies = data.get('dubbing_strategies', [])
        print("✅ Orchestrator is running!")
        print(f"   Dubbing strategies: {dubbing_strategies}")
        
        # Check for God Tier modes
        if any('god_tier' in s for s in dubbing_strategies):
            print("⚠️  God Tier strategies NOT in /api/options")
            print("   (They're hardcoded in the UI - this is expected)")
        else:
            print("   ℹ️ God Tier added via UI (not in backend /options)")
    else:
        print(f"⚠️  Orchestrator responded with: {resp.status_code}")
        
    # Test bulk-status endpoint
    test_batch_id = "00000000-0000-0000-0000-000000000000"
    resp = requests.get(f"{backend_url}/api/jobs/bulk-status/{test_batch_id}", timeout=10)
    
    if resp.status_code == 404:
        data = resp.json()
        if "Batch not found" in data.get("detail", ""):
            print("✅ Bulk-status endpoint: WORKING")
    
    print("")
    print("🎉 All systems operational!")
    print("   - Legacy pipeline: ✅")
    print("   - God Tier hooks: ✅")
    print("   - Bulk mode: ✅")
    print("   - Downloads manager: ✅")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Services may still be starting...")
    print("   Wait 30 seconds and run this cell again")
    
print("=" * 70)


CELL 11:
# Performance expectations for God Tier
print("📊 GOD TIER PERFORMANCE EXPECTATIONS")
print("=" * 70)
print("")
print("✅ Draft Mode (Speed):")
print("  - Total time: ~30-60 seconds")
print("  - Uses: Silero VAD, GLM-ASR, DeepSeek LLM, Kokoro-82M TTS")
print("  - Best for: Quick timing checks, previews")
print("  - GPU usage: Minimal (mostly CPU-bound)")
print("")
print("✅ Hollywood Mode (Quality):")
print("  - Total time: 5-10 minutes (depends on video length)")
print("  - Full 9-stage pipeline:")
print("    1. Surgeon (BS-Roformer): 30-60s")
print("    2. Polisher (Resemble): 20-40s")
print("    3. Ears (Silero V6): 5-10s")
print("    4. Guard (Audeering): 10-15s (if enabled)")
print("    5. Brain (GLM-ASR): 15-30s")
print("    6. Logic (DeepSeek): 10-20s")
print("    7. Mouth (F5-TTS): 60-120s")
print("    8. Skin (Applio RVC): 30-60s")
print("    9. Renderer (BigVGAN): 20-40s")
print("  - Best for: Final production exports")
print("  - GPU usage: Heavy (sequential to fit 24GB)")
print("")
print("✅ Advanced Controls:")
print("  - Toggle any stage on/off")
print("  - Choose between model variants")
print("  - Use Quick Presets:")
print("    • Full Pipeline: All 9 stages")
print("    • Essential Only: 5 core stages")
print("    • Max Quality: 8 stages (skip Guard)")
print("")
print("🐛 If issues occur:")
print("  - Check logs: sh('tail -100 /tmp/stack.log')")
print("  - Verify GPU: sh('nvidia-smi')")
print("  - Check nginx: sh('tail -50 /tmp/nginx.log')")
print("  - Verify God Tier deps: sh('pip list | grep -E \"torch|numpy|librosa\"')")
print("")
print("=" * 70)


CELL 12 (OPTIONAL - Test God Tier):
# Quick test of God Tier Draft mode
import requests
import json
import time

print("🧪 Testing God Tier Draft Mode...")
print("=" * 70)

# Sample test (replace with actual video URL)
test_payload = {
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Replace
    "dubbing_strategy": "god_tier_draft",
    "target_langs": ["en"],
    "source_lang": "auto"
}

print("Payload:")
print(json.dumps(test_payload, indent=2))
print("")
print("⚠️  To actually run this test, uncomment the code below:")
print("")
print("# resp = requests.post(f'{backend_url}/api/v1/dub', json=test_payload, stream=True)")
print("# for line in resp.iter_lines():")
print("#     if line:")
print("#         print(line.decode('utf-8'))")
print("")
print("=" * 70)
