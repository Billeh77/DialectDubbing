"""
Dialogue Isolation Module
Uses Demucs to separate vocals/speech from music and sound effects
"""

import logging
import subprocess
import shutil
import tempfile
from pathlib import Path
import os

logger = logging.getLogger(__name__)


def run(input_wav, output_vocals_wav):
    """
    Isolate vocals/dialogue from audio using Demucs
    
    Args:
        input_wav (Path): Path to input WAV file
        output_vocals_wav (Path): Path to output vocals WAV file
    """
    input_wav = Path(input_wav)
    output_vocals_wav = Path(output_vocals_wav)
    
    if not input_wav.exists():
        raise FileNotFoundError(f"Input file not found: {input_wav}")
    
    # Create output directory if it doesn't exist
    output_vocals_wav.parent.mkdir(parents=True, exist_ok=True)
    
    # Create temporary directory for Demucs output
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Demucs command for vocal separation
        # --two-stems=vocals: Only separate vocals vs everything else
        # -n htdemucs: Use the HT-Demucs model
        # -o: output directory
        cmd = [
            "python", "-m", "demucs.separate",
            "--two-stems=vocals",
            "-n", "htdemucs",
            "-o", str(temp_path),
            str(input_wav)
        ]
        
        logger.info(f"Isolating dialogue from {input_wav}")
        logger.debug(f"Demucs command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.returncode == 0:
                logger.info("✅ Demucs separation completed")
                
                # Find the output vocals file
                # Demucs creates: temp_dir/htdemucs/input_filename/vocals.wav
                input_stem = input_wav.stem  # filename without extension
                vocals_path = temp_path / "htdemucs" / input_stem / "vocals.wav"
                no_vocals_path = temp_path / "htdemucs" / input_stem / "no_vocals.wav"
                
                if vocals_path.exists():
                    # Copy vocals to output location
                    shutil.copy2(vocals_path, output_vocals_wav)
                    logger.info(f"✅ Vocals saved to: {output_vocals_wav}")
                    
                    # Also save the background audio for later use
                    background_path = output_vocals_wav.parent / "audio_background.wav"
                    if no_vocals_path.exists():
                        shutil.copy2(no_vocals_path, background_path)
                        logger.info(f"✅ Background audio saved to: {background_path}")
                    
                    # Check file sizes
                    vocals_size = output_vocals_wav.stat().st_size / (1024*1024)
                    logger.info(f"Output vocals file size: {vocals_size:.2f} MB")
                    
                else:
                    raise RuntimeError(f"Demucs output not found at: {vocals_path}")
            else:
                raise RuntimeError(f"Demucs failed with return code {result.returncode}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Demucs error: {e.stderr}")
            raise RuntimeError(f"Failed to separate audio: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise


def check_demucs():
    """Check if Demucs is available"""
    try:
        result = subprocess.run(
            ["python", "-m", "demucs.separate", "--help"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def run_alternative_method(input_wav, output_vocals_wav):
    """
    Alternative method using ffmpeg for basic vocal isolation
    This is a fallback if Demucs is not available
    """
    input_wav = Path(input_wav)
    output_vocals_wav = Path(output_vocals_wav)
    
    logger.warning("Using alternative vocal isolation method (less accurate)")
    
    # Simple vocal isolation using ffmpeg
    # This is much less accurate than Demucs but might work as a fallback
    cmd = [
        "ffmpeg",
        "-i", str(input_wav),
        "-af", "pan=mono|c0=0.5*c0+-0.5*c1",  # Basic center channel extraction
        "-y", str(output_vocals_wav)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Alternative vocal isolation completed: {output_vocals_wav}")
        else:
            raise RuntimeError(f"FFmpeg failed with return code {result.returncode}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        raise RuntimeError(f"Failed to isolate vocals: {e.stderr}")


if __name__ == "__main__":
    # Test the module
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python isolate_dialogue.py <input.wav> <output_vocals.wav>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    logging.basicConfig(level=logging.INFO)
    
    if not check_demucs():
        logger.warning("Demucs not available, using alternative method")
        try:
            run_alternative_method(input_file, output_file)
        except Exception as e:
            logger.error(f"❌ Alternative method failed: {e}")
            sys.exit(1)
    else:
        try:
            run(input_file, output_file)
            print("✅ Dialogue isolation completed successfully")
        except Exception as e:
            logger.error(f"❌ Dialogue isolation failed: {e}")
            sys.exit(1) 