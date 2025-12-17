@echo off
echo =================================================================
echo 🚀 SETTING UP "GOD TIER" DUBBING PIPELINE
echo =================================================================
echo ⚠️  Ensure you are using Python 3.10.x
echo ⚠️  Ensure CUDA 12.1 is installed
echo =================================================================

:: Check Python version (simple check)
python --version

echo.
echo 📦 Installing Core Dependencies (PyTorch 2.4.0 + CUDA 12.1)...
echo This might take a while...
pip install -r requirements_god_tier.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install core requirements. Exiting.
    exit /b %errorlevel%
)

echo.
echo 👄 Installing F5-TTS (Flow Matching)...
pip install git+https://github.com/SWivid/F5-TTS.git

echo.
echo 🎭 Installing Applio/RVC Utils...
:: Applio is often a standalone app, but for library usage we often install 'rvc-python' or similar.
:: If using the full Applio repo as a library, we might need a specific fork.
:: For now, assuming standard RVC python bindings compatible with Torch 2.x
pip install rvc-python

echo.
echo 🏗️ Setup Complete!
echo =================================================================
echo To start the backend with the new pipeline enabled:
echo 1. Ensure models are downloaded.
echo 2. Run the orchestrator normally.
echo =================================================================
pause
