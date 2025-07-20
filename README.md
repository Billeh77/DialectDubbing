# 🎬 South Park AI Dubbing System

An advanced AI-powered dubbing system that automatically converts South Park episodes from English to Lebanese Arabic. This system uses cutting-edge AI models to extract dialogue, translate it contextually, and synthesize natural-sounding Arabic speech with character-specific voices.

## Features

- ** Video Processing**: Extracts audio from MP4 files using FFmpeg
- ** Dialogue Isolation**: Separates speech from background music/effects using HT-Demucs
- ** Transcription**: High-accuracy transcription with WhisperX
- ** Speaker Diarization**: Identifies different speakers using PyAnnote
- ** Translation**: Context-aware translation to Lebanese Arabic using GPT-4
- ** Speech Synthesis**: Natural-sounding Arabic speech using ElevenLabs
- ** Audio Remixing**: Combines new voices with original background audio
- ** Video Muxing**: Creates final dubbed MP4 with synchronized audio

## System Architecture

```
Input MP4 → Audio Extraction → Dialogue Isolation → Transcription → Translation → Speech Synthesis → Audio Remixing → Video Muxing → Final MP4
```

## Requirements

### System Requirements
- Python 3.8+
- CUDA-compatible GPU (recommended for A100, RTX 4090, etc.)
- FFmpeg installed and accessible in PATH
- At least 8GB RAM
- 10GB+ free disk space

### API Keys Required
- **OpenAI API Key**: For GPT-4 translation
- **ElevenLabs API Key**: For speech synthesis
- **HuggingFace Token**: For PyAnnote speaker diarization

## Installation

### 1. Clone and Setup
```bash
git clone <repository-url>
cd southpark_dub
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Edit `config.py` or set environment variables:
```bash
export OPENAI_API_KEY="your-openai-key"
export ELEVENLABS_API_KEY="your-elevenlabs-key"
export HF_TOKEN="your-huggingface-token"
```

### 4. Setup System
```bash
python interface/upload_interface.py setup
```

## 📁 Project Structure

```
southpark_dub/
├── .venv/                       # Python virtual environment
├── assets/                      # Input videos
│   └── Southpark_short_clip.mp4
├── output/                      # Generated files
│   ├── audio_raw.wav
│   ├── audio_dialogue.wav
│   ├── transcript.csv
│   ├── transcript_ar.csv
│   ├── dubbing_ar.wav
│   └── southpark_lb_dub.mp4
├── modules/                     # Core processing modules
│   ├── extract_audio.py
│   ├── isolate_dialogue.py
│   ├── transcribe.py
│   ├── translate.py
│   ├── synthesize.py
│   ├── remix.py
│   └── mux.py
├── interface/                   # User interfaces
│   └── upload_interface.py
├── main.py                      # Main pipeline orchestrator
├── config.py                    # Configuration settings
└── requirements.txt             # Dependencies
```

## Usage

### Method 1: Command Line Interface

#### Upload and Process Video
```bash
# Upload a video file
python interface/upload_interface.py upload episode.mp4

# Process the video through the dubbing pipeline
python interface/upload_interface.py process

# Check system status
python interface/upload_interface.py status
```

#### Direct Pipeline Execution
```bash
# Run the complete pipeline
python main.py

# Or specify a specific video file
python main.py path/to/video.mp4
```

### Method 2: Web Interface

Launch the Gradio web interface:
```bash
python interface/upload_interface.py web
```

Then open your browser to `http://localhost:7860`

### Method 3: Individual Module Testing

Test specific modules:
```bash
python interface/upload_interface.py test extract
python interface/upload_interface.py test transcribe
python interface/upload_interface.py test translate
```

## 🔧 Configuration

### Character Voice Mapping
Edit `config.py` to customize voice mappings:
```python
CHARACTER_VOICES = {
    "SPEAKER_00": "your-stan-voice-id",
    "SPEAKER_01": "your-kyle-voice-id",
    "SPEAKER_02": "your-cartman-voice-id",
    # ... more mappings
}
```

### Audio Settings
```python
SAMPLE_RATE = 48000
AUDIO_CHANNELS = 1
WHISPER_MODEL = "large-v3"
```

### Translation Settings
```python
TARGET_LANGUAGE = "Lebanese Arabic"
OPENAI_MODEL = "gpt-4o"
TRANSLATION_TEMPERATURE = 0.3
```

## 🔍 Troubleshooting

### Common Issues

#### 1. FFmpeg Not Found
```bash
# Install FFmpeg
# On macOS:
brew install ffmpeg

# On Ubuntu:
sudo apt update && sudo apt install ffmpeg

# On Windows:
# Download from https://ffmpeg.org/download.html
```

#### 2. CUDA Out of Memory
Reduce batch size in `config.py`:
```python
BATCH_SIZE = 8  # Reduce from 16
```

#### 3. API Rate Limits
The system includes automatic rate limiting, but you can adjust:
```python
# In modules/translate.py and modules/synthesize.py
time.sleep(1.0)  # Increase delay between API calls
```

#### 4. Audio Quality Issues
Adjust voice synthesis settings:
```python
VOICE_STABILITY = 0.7
VOICE_SIMILARITY = 0.9
```

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py
```

## 📊 Performance Optimization

### GPU Memory Management
- Use CUDA 12.4+ for better memory efficiency
- Close other GPU applications during processing
- Monitor GPU memory: `nvidia-smi`

### Processing Speed
- Use SSD storage for faster I/O
- Increase `MAX_WORKERS` in config for parallel processing
- Use smaller WhisperX model for faster transcription: `"large-v2"`

### Cost Optimization
- Use `gpt-3.5-turbo` instead of `gpt-4o` for translation
- Batch process multiple episodes
- Cache transcriptions to avoid re-processing

## Testing

### Unit Tests
```bash
# Test individual modules
python -m modules.extract_audio test_input.mp4 test_output.wav
python -m modules.isolate_dialogue test_input.wav test_output.wav
```

### Integration Tests
```bash
# Test complete pipeline with sample video
python main.py assets/sample.mp4
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Performance Metrics

Typical processing times for a 22-minute episode:
- Audio Extraction: ~30 seconds
- Dialogue Isolation: ~2-3 minutes
- Transcription: ~3-5 minutes
- Translation: ~5-10 minutes (depends on API)
- Speech Synthesis: ~10-15 minutes (depends on API)
- Audio Remixing: ~1-2 minutes
- Video Muxing: ~1-2 minutes

**Total: ~25-40 minutes per episode**

## Security & Privacy

- API keys are stored locally and not transmitted
- Temporary files are cleaned up automatically
- No data is stored on external servers (except API calls)
- All processing is done locally

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **OpenAI**: For GPT-4 translation capabilities
- **ElevenLabs**: For high-quality speech synthesis
- **HuggingFace**: For PyAnnote speaker diarization
- **Facebook Research**: For Demucs source separation
- **OpenAI Whisper Team**: For WhisperX transcription

## Support

For issues and questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review existing GitHub issues
3. Create a new issue with detailed logs
4. Join our Discord community (link in repository)

## Updates

The system is actively maintained. Check for updates regularly:
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

**Disclaimer**: This project is for educational and research purposes. Please respect copyright laws and obtain proper permissions before dubbing copyrighted content. 
