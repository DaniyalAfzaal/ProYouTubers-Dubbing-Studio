#!/usr/bin/env python3
"""Verify GPU availability across all services"""

import sys

def check_torch_gpu():
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   GPU count: {torch.cuda.device_count()}")
            print(f"   GPU 0: {torch.cuda.get_device_name(0)}")
            print(f"   GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        return torch.cuda.is_available()
    except Exception as e:
        print(f"❌ PyTorch error: {e}")
        return False

def check_whisperx():
    try:
        import whisperx
        print(f"✅ WhisperX installed")
        return True
    except:
        print(f"❌ WhisperX not available")
        return False

def check_transformers():
    try:
        import transformers
        print(f"✅ Transformers {transformers.__version__}")
        return True
    except:
        print(f"❌ Transformers not available")
        return False

def check_chatterbox():
    try:
        import chatterbox
        print(f"✅ Chatterbox TTS installed")
        return True
    except:
        print(f"❌ Chatterbox not available")
        return False

def check_audio_separator():
    try:
        from audio_separator.separator import Separator
        print(f"✅ Audio Separator installed")
        return True
    except:
        print(f"❌ Audio Separator not available")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GPU Configuration Check")
    print("=" * 60)
    
    gpu_ok = check_torch_gpu()
    whisperx_ok = check_whisperx()
    transformers_ok = check_transformers()
    chatterbox_ok = check_chatterbox()
    separator_ok = check_audio_separator()
    
    print("=" * 60)
    if gpu_ok and whisperx_ok and transformers_ok and chatterbox_ok and separator_ok:
        print("✅ All GPU dependencies ready!")
        sys.exit(0)
    else:
        print("⚠️  Some dependencies missing (may be optional)")
        sys.exit(0 if gpu_ok else 1)
