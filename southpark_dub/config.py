"""
Configuration file for South Park AI Dubbing System
Contains all constants, API keys, file paths, and runtime settings
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
MODULES_DIR = BASE_DIR / "modules"

# File paths
# ---> IMPORTANT: Replace "your_video_here.mp4" with the actual name of your video file.
# ---> Make sure the video is placed inside the 'southpark_dub/assets/' directory.
INPUT_MP4 = ASSETS_DIR / "Southpark_short_clip.mp4"
AUDIO_RAW = OUTPUT_DIR / "audio_raw.wav"
AUDIO_DIALOGUE = OUTPUT_DIR / "audio_dialogue.wav"
AUDIO_BACKGROUND = OUTPUT_DIR / "audio_background.wav"
TRANSCRIPT_CSV = OUTPUT_DIR / "transcript.csv"
TRANSCRIPT_AR_CSV = OUTPUT_DIR / "transcript_ar.csv"
DUBBING_AR_WAV = OUTPUT_DIR / "dubbing_ar.wav"
M_E_BED = OUTPUT_DIR / "m_e_bed.wav"
MIX_WAV = OUTPUT_DIR / "mix.wav"
FINAL_MP4 = OUTPUT_DIR / "southpark_lb_dub.mp4"

# Audio settings
SAMPLE_RATE = 48000
AUDIO_CHANNELS = 1
AUDIO_FORMAT = "wav"

# Model settings
WHISPER_MODEL = "large-v3"
DEMUCS_MODEL = "htdemucs"
DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"
EMBEDDING_MODEL = "pyannote/embedding"

# API Keys - Replace with your actual keys
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_f78bdf6d5edc1c0d91be97c33b9dac380be4f924c395b38e")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
HF_TOKEN = os.getenv("HF_TOKEN", "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")

# Translation settings
TARGET_LANGUAGE = "Lebanese Arabic"
OPENAI_MODEL = "gpt-4o"
TRANSLATION_TEMPERATURE = 0.3

# ElevenLabs settings
ELEVENLABS_MODEL = "eleven_multilingual_v2"
VOICE_STABILITY = 0.5
VOICE_SIMILARITY = 0.8
VOICE_STYLE = 0.0
VOICE_BOOST = True

# Character voice mappings (placeholder voice IDs from ElevenLabs)
# The script will identify speakers as SPEAKER_00, SPEAKER_01, etc.
# For a high-quality dub, you should map these to specific Voice IDs from your ElevenLabs account.
# For a first test, the default placeholders below will be used.
CHARACTER_VOICES = {
    "SPEAKER_00": "21m00Tcm4TlvDq8ikWAM",  # Stan (placeholder)
    "SPEAKER_01": "AZnzlk1XvdvUeBnXmlld",  # Kyle (placeholder)
    "SPEAKER_02": "EXAVITQu4vr4xnSDxMaL",  # Cartman (placeholder)
    "SPEAKER_03": "ErXwobaYiN019PkySvjV",  # Kenny (placeholder)
    "SPEAKER_04": "MF3mGyEYCl7XYWbV9V6O",  # Randy (placeholder)
    "SPEAKER_05": "TxGEqnHWrfWFTfGW9XjX",  # Butters (placeholder)
    "default": "21m00Tcm4TlvDq8ikWAM"     # Default voice if a speaker is not in this map
}

# Processing settings
CHUNK_SIZE = 1024
MAX_WORKERS = 4
DEVICE = "auto"  # Will be set to "mps", "cuda", or "cpu" based on availability
BATCH_SIZE = 16

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Device detection function
def get_device():
    """Automatically detect the best available device"""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"  # Apple Silicon GPU
        else:
            return "cpu"
    except ImportError:
        return "cpu"

# Set device based on availability
if DEVICE == "auto":
    DEVICE = get_device()

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True) 