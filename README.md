# ProYouTubers Dubbing Studio

![ProYouTubers Logo](apps/frontend/assets/ProYouTubers-Logo.jpg)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![uv](https://img.shields.io/badge/Package_Manager-uv-black?logo=astral&logoColor=white)](https://docs.astral.sh/uv/)
[![FFmpeg](https://img.shields.io/badge/Powered_by-FFmpeg-red?logo=ffmpeg)](https://ffmpeg.org/)

> 🎯 *Winning isn't everything, but wanting to win is.*

---

**ProYouTubers Dubbing Studio** is a professional, GPU-accelerated pipeline for **automatic video dubbing** and **subtitle generation**.
It integrates cutting-edge AI models for **ASR** (Automatic Speech Recognition), **translation**, and **TTS** (Text-to-Speech), featuring:

* 🎬 **L4 GPU acceleration** for 6x faster processing
* 🌍 **11 translation providers** including DeepL, Google, ChatGPT
* 🎙️ **WhisperX Large-v3** for best-in-class transcription
* 🎨 **Premium web interface** with real-time progress tracking
* 🔧 **Audio source separation** for crystal-clear vocals
* ⚡ **VAD-based alignment** for perfect timing
* 🎯 **Multiple dubbing strategies** for natural results

---

## 🚀 Features

### Core Capabilities
* **End-to-End Dubbing:** From video/audio input to fully dubbed output with burned-in subtitles
* **GPU-Accelerated:** NVIDIA L4 GPU support for lightning-fast processing
* **REST API & CLI:** FastAPI endpoints and command-line tools for automation
* **Premium Web UI:** Modern interface with live progress tracking and involve mode
* **Modular Architecture:** Easily plug, swap, or extend ASR, translation, and TTS models

### Advanced Features
* **Multiple Translation Providers:**
  - DeepL (premium quality)
  - Google Translator (free)
  - Microsoft Azure
  - ChatGPT (context-aware)
  - Facebook M2M100 (offline, GPU)
  - + 6 more providers

* **Flexible Translation:** Segment-wise or full-text with smart synchronization
* **Advanced Audio Processing:** Source separation, VAD trimming, Rubberband time-stretching
* **Subtitle Generation:** Netflix-style, bold-desktop, or mobile-optimized (SRT/VTT/ASS)
* **Interactive Review:** Manual review at transcription, alignment, and TTS stages

---

## 🗂️ Project Structure

```bash
proyoutubers-dubbing-studio/
├── apps/
│   ├── backend/
│   │   ├── cache/              # Cached audio/background/intermediate data
│   │   ├── libs/
│   │   │   └── common-schemas/ # Shared Pydantic models & utilities
│   │   ├── models_cache/       # Downloaded AI models (ASR, TTS, etc.)
│   │   └── services/
│   │       ├── asr/            # Speech recognition (WhisperX Large-v3)
│   │       ├── translation/    # 11 translation providers
│   │       ├── tts/            # Text-to-speech (Chatterbox, Edge TTS)
│   │       └── orchestrator/   # Main pipeline coordinator
│   └── frontend/               # Premium web interface (red/white/black theme)
│       ├── assets/             # ProYouTubers branding assets
│       ├── scripts/            # JavaScript modules
│       └── styles/             # Premium CSS with gradients & animations
├── Modal_cells.md             # Modal.com GPU deployment guide
├── Makefile                   # Build & run commands
└── README.md                  # This file
```

---

## 📋 Requirements

- **Python 3.11+**
- **FFmpeg** (with libx264, AAC support)
- **Rubberband CLI** (for time-stretching)
- **SOX** (audio processing)
- **espeak-ng** (phoneme support)
- **uv** (fast package manager) - *recommended*

### GPU Requirements (Optional but Recommended)
- **NVIDIA GPU** with 24GB+ VRAM (L4, A10, RTX 4090, etc.)
- **CUDA 12.1+**
- **cuDNN 8+**

---

## 🔧 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/YourUsername/ProYouTubers-Dubbing-Studio.git
cd ProYouTubers-Dubbing-Studio
```

### 2. Set Up Environment
```bash
# Copy environment template
cp .env.example .env

# Add your API keys:
# - HF_TOKEN (Hugging Face)
# - DEEPL_API_KEY (optional, for premium translation)
```

### 3. Install Dependencies
```bash
# Using Makefile (recommended)
make install-dep

# Or manually:
cd apps/backend/services/asr && uv sync
cd ../translation && uv sync
cd ../tts && uv sync
cd ../orchestrator && uv sync
```

### 4. Start Services
```bash
# Start all backend services + UI
make dev

# Or start individually:
make stack-up     # Backend services only
make ui           # Web UI only
```

### 5. Access Web Interface
Open browser to: **http://localhost:5173**

---

## 🚀 Modal.com GPU Deployment

For **6x faster processing** with L4 GPU:

1. Install Modal:
```bash
pip install modal
python -m modal setup
```

2. Run all cells in `Modal_cells.md` sequentially in a Jupyter notebook

3. Access via Modal tunnel URL

**Expected Performance:**
- CPU: 6-9 minutes per video
- **L4 GPU: 1-1.5 minutes per video** ⚡

---

## 🎯 Usage Examples

### Web Interface
1. Upload video or paste URL
2. Select target language(s)
3. Choose translation provider (DeepL recommended)
4. Configure options (audio separation, etc.)
5. Click "Start Dubbing"
6. Download results!

### API Example
```python
import requests

# Upload and dub a video
with open('video.mp4', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/dub',
        files={'file': f},
        data={
            'target_lang': 'fr',
            'tr_model': 'deepl',  # Use DeepL for best quality
            'audio_sep': 'true',
            'involve_mode': 'false'
        }
    )

result = response.json()
print(f"Dubbed video: {result['video_url']}")
```

---

## 🤖 Supported Models

### ASR (Speech Recognition)
- **WhisperX Large-v3** (default, GPU-optimized)
- WhisperX Medium, Small (fallback options)

### Translation
| Provider | Quality | Cost | Languages |
|----------|---------|------|-----------|
| **DeepL** | ⭐⭐⭐⭐⭐ | $5/mo* | 31 |
| **Google** | ⭐⭐⭐ | Free | 100+ |
| **ChatGPT** | ⭐⭐⭐⭐⭐ | $0.002/1K | 50+ |
| **Microsoft** | ⭐⭐⭐⭐ | $10/mo* | 100+ |
| **M2M100** | ⭐⭐⭐⭐ | Free (offline) | 100 |
| + 6 more | Varies | Varies | Varies |

*Free tiers available

### TTS (Text-to-Speech)
- **Chatterbox Multilingual** (GPU-accelerated)
- **Edge TTS** (Microsoft voices)

---

## ⚙️ Configuration

### GPU Settings (`.env`)
```bash
# WhisperX GPU Configuration
WHISPERX_DEVICE=cuda
WHISPERX_MODEL_NAME=large-v3
WHISPERX_BATCH_SIZE=8
WHISPERX_COMPUTE_TYPE=float16

# DeepL API (optional)
DEEPL_API_KEY=your-key-here
```

### Translation Provider Selection
Set in UI or via API:
```python
data = {
    'tr_model': 'deepl',  # or 'google', 'chatgpt', 'microsoft', etc.
}
```

---

## 🎨 Premium Features

### Web Interface Highlights
- **Red/White/Black Theme** - Professional, competitive design
- **Dark/Light Mode** - Automatic or manual toggle
- **Real-time Progress** - SSE-powered live updates
- **Interactive Review** - Manual editing at key stages
- **GPU Monitoring** - Real-time performance metrics
- **Responsive Design** - Works on desktop, tablet, mobile

### Audio Processing
- **Source Separation** - Isolate vocals using neural networks
- **VAD Trimming** - Remove silence for natural pacing
- **Time Stretching** - Rubberband for high-quality alignment
- **Smart Concatenation** - Weighted silence padding

---

## 📚 Documentation

- **[API Reference](docs/API.md)** - REST API endpoints
- **[Translation Guide](artifacts/translation_services_guide.md)** - All 11 providers
- **[GPU Optimization](artifacts/walkthrough.md)** - L4 GPU setup
- **[Modal Deployment](Modal_cells.md)** - Cloud GPU deployment

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific service tests
cd apps/backend/services/asr && uv run pytest
cd apps/backend/services/orchestrator && uv run pytest
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see [LICENSE](LICENSE) file for details.

---

## 🌐 About ProYouTubers

**ProYouTubers** helps content creators scale their reach globally with AI-powered dubbing and translation tools.

- **Website:** [https://proyoutubers.com](https://proyoutubers.com)
- **Email:** [info@proyoutubers.com](mailto:info@proyoutubers.com)

---

## 🙏 Acknowledgments

Built with:
- [WhisperX](https://github.com/m-bain/whisperX) - Fast ASR with word-level timestamps
- [Chatterbox](https://github.com/Your-Repo/chatterbox) - Multilingual TTS
- [deep-translator](https://github.com/nidhaloff/deep-translator) - Translation providers
- [FFmpeg](https://ffmpeg.org/) - Media processing
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Modal](https://modal.com/) - Serverless GPU infrastructure

---

## ⭐ Star Us!

If this project helps you, please give it a ⭐ on GitHub!

**ProYouTubers Dubbing Studio** - *Winning isn't everything, but wanting to win is.*
