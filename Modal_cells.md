
CELL 1:
%uv pip install -U modal requests
!python -m modal setup


CELL 2:
import modal

app = modal.App.lookup('proyoutubers-dubbing-modal', create_if_missing=True)

# Use Modal's CUDA image with PyTorch pre-installed (includes cuDNN)
proyoutubers_image = (
    modal.Image.from_registry("nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04", add_python="3.11")
    .apt_install(
        'git','make','ffmpeg','rubberband-cli','libsndfile1',
        'openjdk-17-jre-headless','ca-certificates','curl',
        'espeak-ng','sox','libsox-fmt-all','nginx',
        'build-essential','python3-dev'  # For compiling C extensions (diffq)
    )
    .pip_install('uv>=0.5.0')
    # Install PyTorch with CUDA 12.1 support
    .run_commands(
        'pip install torch==2.5.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu121',
        'python -c "import torch; print(f\\"PyTorch {torch.__version__} with CUDA {torch.version.cuda}\\")"'
    )
)

# Your Hugging Face token (required)
HF_TOKEN = 'hf_REDACTED_FOR_SECURITY'
hf_secret = modal.Secret.from_dict({'HF_TOKEN': HF_TOKEN})

# DeepL API key (optional - for better translation quality)
# Get your free API key from: https://www.deepl.com/pro-api
# Leave empty to use free Google Translator instead
DEEPL_API_KEY = ''  # Optional: Add your DeepL API key here
deepl_secret = modal.Secret.from_dict({'DEEPL_API_KEY': DEEPL_API_KEY}) if DEEPL_API_KEY else None

print("Modal app, image and secret configured with CUDA + cuDNN support.")
if DEEPL_API_KEY:
    print("✅ DeepL API key configured for premium translation.")
else:
    print("ℹ️  No DeepL API key - will use free Google Translator.")


CELL 3:
# L4 GPU configuration for 5-7x faster processing
with modal.enable_output():
    # Build secrets list - add DeepL if configured
    secrets_list = [hf_secret]
    if deepl_secret:
        secrets_list.append(deepl_secret)
    
    sb = modal.Sandbox.create(
        'bash','-lc','sleep infinity',
        app=app,
        image=proyoutubers_image,
        secrets=secrets_list,  # Dynamic secrets list
        encrypted_ports=[8000, 5173],  # orchestrator and UI
        cpu=4,           # Reduced CPU (GPU handles heavy compute)
        memory=24576,    # 24 GiB RAM for GPU model loading
        gpu="L4",        # NVIDIA L4 with 24GB VRAM (new syntax)
        timeout=3*60*60,     # 3h lifetime
        idle_timeout=60*60,  # 1h idle timeout
        verbose=True,
    )
print("Sandbox created with L4 GPU:", sb.object_id)


CELL 4:
def sh(cmd: str, timeout: int|None = None):
    proc = sb.exec('bash','-lc', cmd, timeout=timeout) if timeout else sb.exec('bash','-lc', cmd)
    out = proc.stdout.read()
    err = proc.stderr.read()
    if out: print(out)
    if err: print(err)
    return proc

print("Helper defined.")


CELL 5:
# Clone ProYouTubers Dubbing Studio repository
REPO_URL = 'https://github.com/DaniyalAfzaal/ProYouTubers-Dubbing-Studio.git'

# Clone the latest version
sh(f'cd /root && rm -rf proyoutubers-dubbing && git clone --depth 1 {REPO_URL} proyoutubers-dubbing')

# Copy .env.example -> .env and inject your HF_TOKEN
sh(r'''
cd /root/proyoutubers-dubbing
cp -f .env.example .env
# Replace HF_TOKEN=... in .env with the secret from Modal (available via $HF_TOKEN)
sed -i "s/^HF_TOKEN=.*/HF_TOKEN=$HF_TOKEN/" .env
''')

print("Repository cloned and .env configured.")

CELL 6:
# Build venvs for ASR, translation, TTS, orchestrator
sh('cd /root/proyoutubers-dubbing && make install-dep', timeout=60*60)
print("Dependencies installed.")

# Verify GPU is available
print("\n" + "="*60)
print("Verifying GPU configuration...")
print("="*60)
sh(r'''
cd /root/proyoutubers-dubbing
python3 -c "
import torch
print(f'✅ PyTorch {torch.__version__}')
print(f'   CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'   CUDA version: {torch.version.cuda}')
    print(f'   GPU count: {torch.cuda.device_count()}')
    print(f'   GPU 0: {torch.cuda.get_device_name(0)}')
    print(f'   GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
else:
    print('   ⚠️  WARNING: CUDA not available!')
"
''')

CELL 7:
# Start services without reload.  The Makefile uses $(RELOAD) so override it to empty.
sh('cd /root/proyoutubers-dubbing && nohup make RELOAD= stack-up > /tmp/stack.log 2>&1 &')
print("Backend services starting…")


CELL 8:
# Write nginx config.  Runs as root for file access, 500MB uploads, 10m proxy timeouts.
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

    location / {
      try_files $uri $uri/ /index.html;
    }
  }
}
NG
''')

# Start nginx
sh('nohup nginx -c /tmp/nginx.conf -g "daemon off;" > /tmp/nginx.log 2>&1 &')
print("Nginx launched.")


CELL 9:
# Show the tunnel endpoints for backend (8000) and UI (5173)
tunnels = sb.tunnels()
backend_url = tunnels[8000].url.rstrip('/')
ui_url = tunnels[5173].url.rstrip('/')

print("✅ Backend URL:", backend_url)
print("✅ UI URL:", ui_url)
print("Open the UI URL in your browser.  If cached, press Ctrl+F5 to reload.")
