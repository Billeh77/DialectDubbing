"""
Audio Extraction Module
Extracts audio from MP4 video files using FFmpeg
"""

import logging
import subprocess
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def run(input_mp4, output_wav):
    """
    Extract audio from MP4 file and save as WAV
    
    Args:
        input_mp4 (Path): Path to input MP4 file
        output_wav (Path): Path to output WAV file
    """
    input_mp4 = Path(input_mp4)
    output_wav = Path(output_wav)
    
    if not input_mp4.exists():
        raise FileNotFoundError(f"Input file not found: {input_mp4}")
    
    # Create output directory if it doesn't exist
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    
    # FFmpeg command to extract audio
    # -i: input file
    # -ac 1: mono audio (1 channel)
    # -ar 48000: 48kHz sample rate
    # -f wav: output format
    # -y: overwrite output file if it exists
    cmd = [
        "ffmpeg",
        "-i", str(input_mp4),
        "-ac", "1",
        "-ar", "48000", 
        "-f", "wav",
        "-y", str(output_wav)
    ]
    
    logger.info(f"Extracting audio from {input_mp4} to {output_wav}")
    logger.debug(f"FFmpeg command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Audio extracted successfully: {output_wav}")
            
            # Check if output file was created and has content
            if output_wav.exists() and output_wav.stat().st_size > 0:
                logger.info(f"Output file size: {output_wav.stat().st_size / (1024*1024):.2f} MB")
            else:
                raise RuntimeError("Output file was not created or is empty")
        else:
            raise RuntimeError(f"FFmpeg failed with return code {result.returncode}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        raise RuntimeError(f"Failed to extract audio: {e.stderr}")
    except FileNotFoundError:
        logger.error("FFmpeg not found. Please install FFmpeg and ensure it's in your PATH")
        raise RuntimeError("FFmpeg not found. Please install FFmpeg")


def check_ffmpeg():
    """Check if FFmpeg is available"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


if __name__ == "__main__":
    # Test the module
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python extract_audio.py <input.mp4> <output.wav>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    logging.basicConfig(level=logging.INFO)
    
    if not check_ffmpeg():
        logger.error("FFmpeg not found")
        sys.exit(1)
    
    try:
        run(input_file, output_file)
        print("✅ Audio extraction completed successfully")
    except Exception as e:
        logger.error(f"❌ Audio extraction failed: {e}")
        sys.exit(1) 