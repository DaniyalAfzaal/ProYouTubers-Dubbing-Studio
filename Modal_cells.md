
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
        'build-essential','python3-dev','clang'  # Compiler tools for building C extensions
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
# GPU configuration - Customize GPU type and timeouts
# Available GPU types: "T4", "L4", "A10G", "A100" (check Modal pricing for costs)
GPU_TYPE = "L4"  # Change to "T4" for cheaper, "A100" for faster

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
        volumes={"/persistent-outputs": outputs_volume},  # 🆕 Persistent storage
        cpu=4,           # Reduced CPU (GPU handles heavy compute)
        memory=24576,    # 24 GiB RAM for GPU model loading
        gpu=GPU_TYPE,    # Customizable GPU type
        timeout=3*60*60,     # 3h max lifetime
        idle_timeout=3*60,   # 3min idle timeout (cost savings!)
        verbose=True,
    )
print(f"Sandbox created with {GPU_TYPE} GPU + persistent volume:", sb.object_id)
print("⚡ Idle timeout: 3 minutes - GPU auto-releases for cost savings")


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


CELL 5A:
# Pull latest code with CUDA fix and bulk mode validation fix
sh(r'''
cd /root/proyoutubers-dubbing
git pull origin main
''')

print("✅ Code updated with latest fixes:")
print("  - CUDA alignment fix (GPU acceleration)")
print("  - Bulk mode validation fix")
print("  - UI improvements")


CELL 5B:
# Create Chatterbox TTS config to fix timing issues
sh(r'''
mkdir -p /root/proyoutubers-dubbing/apps/backend/model_config
cat > /root/proyoutubers-dubbing/apps/backend/model_config/chatterbox.yaml << 'EOF'
params:
  generate:
    guidance_scale: 3.5
    temperature: 0.7
    max_length: 1000
EOF
''')

print("✅ Chatterbox TTS config created")
print("🎯 This fixes:")
print("  - TTS generating 62s for 30s segments")
print("  - Audio timing mismatches")
print("  - Robotic voice from time-stretching")


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


CELL 9:
# Show the tunnel endpoints for backend (8000) and UI (5173)
tunnels = sb.tunnels()
backend_url = tunnels[8000].url.rstrip('/')
ui_url = tunnels[5173].url.rstrip('/')

print("✅ Backend URL:", backend_url)
print("✅ UI URL:", ui_url)
print("Open the UI URL in your browser.  If cached, press Ctrl+F5 to reload.")


CELL 10:
# Verification guide - check after deployment
print("🔍 After running a dubbing job, check logs for:")
print("")
print("✅ Expected improvements:")
print("  1. NO 'Failed to load alignment model on CUDA' warning")
print("  2. Alignment: ~4-5s (not 19s+)")
print("  3. TTS segment generation: <20s each (not 62s)")
print("  4. Time stretch ratio: <1.1x (not 1.17x)")
print("  5. Bulk mode accepts target languages without error")
print("")
print("📊 Performance targets:")
print("  - ASR total: 80-100s (vs 120s+)")
print("  - TTS per segment: 15-20s (vs 62s)")
print("  - Voiceover quality: Natural (vs robotic)")
print("")
print("🐛 If issues persist:")
print("  - Check logs: sh('tail -100 /tmp/stack.log')")
print("  - Verify GPU: sh('nvidia-smi')")
print("  - Increase TTS guidance_scale to 4.0-4.5 in config")
