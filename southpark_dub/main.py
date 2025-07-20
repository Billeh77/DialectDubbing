#!/usr/bin/env python3
"""
South Park AI Dubbing System - Main Pipeline Orchestrator
Runs the complete dubbing pipeline from MP4 input to final Arabic dubbed output
"""

import logging
import time
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("output/pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import configuration and modules
from config import *
from modules import extract_audio, isolate_dialogue, transcribe, translate, synthesize, remix, mux


def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        import torch
        import whisperx
        import demucs
        import openai
        import elevenlabs
        import moviepy
        logger.info("✅ All required dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        return False


def check_input_file():
    """Check if input MP4 file exists"""
    if not INPUT_MP4.exists():
        logger.error(f"❌ Input file not found: {INPUT_MP4}")
        logger.info(f"Please place your South Park MP4 file at: {INPUT_MP4}")
        return False
    logger.info(f"✅ Input file found: {INPUT_MP4}")
    return True


def check_api_keys():
    """Check if API keys are configured"""
    missing_keys = []
    
    if ELEVENLABS_API_KEY == "your-elevenlabs-key-here":
        missing_keys.append("ELEVENLABS_API_KEY")
    
    if OPENAI_API_KEY == "your-openai-key-here":
        missing_keys.append("OPENAI_API_KEY")
    
    if HF_TOKEN == "your-huggingface-token-here":
        missing_keys.append("HF_TOKEN")
    
    if missing_keys:
        logger.warning(f"⚠️ Missing API keys: {', '.join(missing_keys)}")
        logger.info("Set them as environment variables or update config.py")
        return False
    
    logger.info("✅ All API keys configured")
    return True


def run_pipeline():
    """Run the complete dubbing pipeline"""
    start_time = time.time()
    
    logger.info("🚀 Starting South Park AI Dubbing Pipeline")
    logger.info("="*60)
    
    # Pre-flight checks
    if not check_dependencies():
        logger.error("❌ Dependency check failed")
        return False
    
    if not check_input_file():
        logger.error("❌ Input file check failed")
        return False
    
    if not check_api_keys():
        logger.warning("⚠️ API keys not configured - some steps may fail")
    
    try:
        # Step 1: Extract audio from MP4
        logger.info("📹 Step 1: Extracting audio from MP4...")
        step_start = time.time()
        extract_audio.run(INPUT_MP4, AUDIO_RAW)
        logger.info(f"✅ Audio extraction completed in {time.time() - step_start:.2f}s")
        
        # Step 2: Isolate dialogue using Demucs
        logger.info("🎤 Step 2: Isolating dialogue from background...")
        step_start = time.time()
        isolate_dialogue.run(AUDIO_RAW, AUDIO_DIALOGUE)
        logger.info(f"✅ Dialogue isolation completed in {time.time() - step_start:.2f}s")
        
        # Step 3: Transcribe and diarize
        logger.info("✍️ Step 3: Transcribing and performing speaker diarization...")
        step_start = time.time()
        transcribe.run(AUDIO_DIALOGUE, TRANSCRIPT_CSV)
        logger.info(f"✅ Transcription completed in {time.time() - step_start:.2f}s")
        
        # Step 4: Translate to Lebanese Arabic
        logger.info("🌍 Step 4: Translating to Lebanese Arabic...")
        step_start = time.time()
        translate.run(TRANSCRIPT_CSV, TRANSCRIPT_AR_CSV)
        logger.info(f"✅ Translation completed in {time.time() - step_start:.2f}s")
        
        # Step 5: Synthesize Arabic speech
        logger.info("🎙️ Step 5: Synthesizing Arabic speech...")
        step_start = time.time()
        synthesize.run(TRANSCRIPT_AR_CSV, DUBBING_AR_WAV)
        logger.info(f"✅ Speech synthesis completed in {time.time() - step_start:.2f}s")
        
        # Step 6: Remix audio (combine new voices with background)
        logger.info("🎚️ Step 6: Remixing audio tracks...")
        step_start = time.time()
        remix.run(AUDIO_RAW, AUDIO_DIALOGUE, DUBBING_AR_WAV, M_E_BED, MIX_WAV)
        logger.info(f"✅ Audio remixing completed in {time.time() - step_start:.2f}s")
        
        # Step 7: Mux final video
        logger.info("📼 Step 7: Muxing final video...")
        step_start = time.time()
        mux.run(INPUT_MP4, MIX_WAV, FINAL_MP4)
        logger.info(f"✅ Video muxing completed in {time.time() - step_start:.2f}s")
        
        total_time = time.time() - start_time
        logger.info("="*60)
        logger.info(f"🎉 Pipeline completed successfully in {total_time:.2f}s")
        logger.info(f"📁 Final dubbed video saved to: {FINAL_MP4}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}")
        logger.exception("Full error traceback:")
        return False


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # If a file path is provided as argument, use it
        global INPUT_MP4
        INPUT_MP4 = Path(sys.argv[1])
    
    success = run_pipeline()
    
    if success:
        logger.info("✅ Dubbing pipeline completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Dubbing pipeline failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 