"""
Audio Remixing Module
Combines Arabic voices with background music and effects
"""

import logging
import subprocess
import numpy as np
import soundfile as sf
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


def run(original_wav, dialogue_wav, dubbing_wav, output_m_e_bed, output_mix):
    """
    Remix audio by combining new Arabic voices with background music and effects
    
    Args:
        original_wav (Path): Path to original full audio
        dialogue_wav (Path): Path to isolated dialogue audio
        dubbing_wav (Path): Path to Arabic dubbed audio
        output_m_e_bed (Path): Path to output music+effects bed
        output_mix (Path): Path to final mixed output
    """
    original_wav = Path(original_wav)
    dialogue_wav = Path(dialogue_wav)
    dubbing_wav = Path(dubbing_wav)
    output_m_e_bed = Path(output_m_e_bed)
    output_mix = Path(output_mix)
    
    # Check input files exist
    for file_path in [original_wav, dialogue_wav, dubbing_wav]:
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
    
    # Create output directories
    output_m_e_bed.parent.mkdir(parents=True, exist_ok=True)
    output_mix.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("🎚️ Starting audio remixing process")
    
    try:
        # Step 1: Create music+effects bed by subtracting dialogue from original
        logger.info("Step 1: Creating music+effects bed...")
        create_music_effects_bed(original_wav, dialogue_wav, output_m_e_bed)
        
        # Step 2: Mix the Arabic dubbing with the M+E bed
        logger.info("Step 2: Mixing Arabic voices with background...")
        mix_audio_tracks(output_m_e_bed, dubbing_wav, output_mix)
        
        logger.info("✅ Audio remixing completed successfully")
        
    except Exception as e:
        logger.error(f"Audio remixing failed: {e}")
        raise


def create_music_effects_bed(original_wav, dialogue_wav, output_m_e_bed):
    """
    Create music+effects bed by subtracting dialogue from original audio
    
    Args:
        original_wav (Path): Path to original full audio
        dialogue_wav (Path): Path to isolated dialogue audio
        output_m_e_bed (Path): Path to output music+effects bed
    """
    logger.info(f"Creating M+E bed from {original_wav} and {dialogue_wav}")
    
    # Method 1: Try using FFmpeg for audio subtraction
    try:
        cmd = [
            "ffmpeg",
            "-i", str(original_wav),
            "-i", str(dialogue_wav),
            "-filter_complex", "[0:a][1:a]amerge=inputs=2[out];[out]pan=mono|c0=c0-c1[final]",
            "-map", "[final]",
            "-y", str(output_m_e_bed)
        ]
        
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.returncode == 0:
            logger.info("✅ M+E bed created using FFmpeg")
            return
            
    except subprocess.CalledProcessError as e:
        logger.warning(f"FFmpeg method failed: {e.stderr}")
        logger.info("Falling back to manual audio subtraction...")
    
    # Method 2: Manual audio subtraction using numpy
    try:
        # Load audio files
        original_audio, sr_orig = sf.read(original_wav)
        dialogue_audio, sr_dial = sf.read(dialogue_wav)
        
        # Ensure mono
        if len(original_audio.shape) > 1:
            original_audio = np.mean(original_audio, axis=1)
        if len(dialogue_audio.shape) > 1:
            dialogue_audio = np.mean(dialogue_audio, axis=1)
        
        # Ensure same sample rate
        if sr_orig != sr_dial:
            logger.warning(f"Sample rate mismatch: {sr_orig} vs {sr_dial}")
            # Resample dialogue to match original
            from scipy.signal import resample
            dialogue_audio = resample(dialogue_audio, int(len(dialogue_audio) * sr_orig / sr_dial))
        
        # Ensure same length
        min_length = min(len(original_audio), len(dialogue_audio))
        original_audio = original_audio[:min_length]
        dialogue_audio = dialogue_audio[:min_length]
        
        # Subtract dialogue from original (with scaling factor)
        # Scale down the dialogue subtraction to avoid over-cancellation
        dialogue_scale = 0.7
        m_e_bed = original_audio - (dialogue_audio * dialogue_scale)
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(m_e_bed))
        if max_val > 0:
            m_e_bed = m_e_bed / max_val * 0.95
        
        # Save M+E bed
        sf.write(output_m_e_bed, m_e_bed, sr_orig)
        
        logger.info("✅ M+E bed created using manual subtraction")
        
    except Exception as e:
        logger.error(f"Manual subtraction failed: {e}")
        
        # Fallback: Use original audio as M+E bed (less ideal)
        logger.warning("Using original audio as M+E bed (fallback)")
        
        # Copy original to M+E bed location
        import shutil
        shutil.copy2(original_wav, output_m_e_bed)


def mix_audio_tracks(m_e_bed_wav, dubbing_wav, output_mix):
    """
    Mix the music+effects bed with the Arabic dubbing
    
    Args:
        m_e_bed_wav (Path): Path to music+effects bed
        dubbing_wav (Path): Path to Arabic dubbed audio
        output_mix (Path): Path to final mixed output
    """
    logger.info(f"Mixing {m_e_bed_wav} with {dubbing_wav}")
    
    # Method 1: Try using FFmpeg for mixing
    try:
        cmd = [
            "ffmpeg",
            "-i", str(m_e_bed_wav),
            "-i", str(dubbing_wav),
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=longest:weights=0.7 0.8",
            "-y", str(output_mix)
        ]
        
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.returncode == 0:
            logger.info("✅ Audio mixing completed using FFmpeg")
            return
            
    except subprocess.CalledProcessError as e:
        logger.warning(f"FFmpeg mixing failed: {e.stderr}")
        logger.info("Falling back to manual audio mixing...")
    
    # Method 2: Manual audio mixing using numpy
    try:
        # Load audio files
        m_e_audio, sr_me = sf.read(m_e_bed_wav)
        dubbing_audio, sr_dub = sf.read(dubbing_wav)
        
        # Ensure mono
        if len(m_e_audio.shape) > 1:
            m_e_audio = np.mean(m_e_audio, axis=1)
        if len(dubbing_audio.shape) > 1:
            dubbing_audio = np.mean(dubbing_audio, axis=1)
        
        # Ensure same sample rate
        if sr_me != sr_dub:
            logger.warning(f"Sample rate mismatch: {sr_me} vs {sr_dub}")
            # Resample dubbing to match M+E
            from scipy.signal import resample
            dubbing_audio = resample(dubbing_audio, int(len(dubbing_audio) * sr_me / sr_dub))
        
        # Ensure same length (pad shorter with zeros)
        max_length = max(len(m_e_audio), len(dubbing_audio))
        
        if len(m_e_audio) < max_length:
            m_e_audio = np.pad(m_e_audio, (0, max_length - len(m_e_audio)), 'constant', constant_values=0)
        if len(dubbing_audio) < max_length:
            dubbing_audio = np.pad(dubbing_audio, (0, max_length - len(dubbing_audio)), 'constant', constant_values=0)
        
        # Mix the audio tracks with appropriate weights
        m_e_weight = 0.7  # Slightly reduce background
        dubbing_weight = 0.8  # Slightly emphasize voices
        
        mixed_audio = (m_e_audio * m_e_weight) + (dubbing_audio * dubbing_weight)
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(mixed_audio))
        if max_val > 0:
            mixed_audio = mixed_audio / max_val * 0.95
        
        # Save mixed audio
        sf.write(output_mix, mixed_audio, sr_me)
        
        logger.info("✅ Audio mixing completed using manual method")
        
    except Exception as e:
        logger.error(f"Manual mixing failed: {e}")
        raise


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


def validate_remix(output_file):
    """
    Validate the remixed audio file
    
    Args:
        output_file (Path): Path to output file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        output_file = Path(output_file)
        
        if not output_file.exists():
            logger.error(f"Output file not found: {output_file}")
            return False
        
        # Check file size
        file_size = output_file.stat().st_size
        if file_size == 0:
            logger.error("Output file is empty")
            return False
        
        # Load and check audio
        audio_data, sample_rate = sf.read(output_file)
        
        # Check duration
        duration = len(audio_data) / sample_rate
        if duration < 1.0:
            logger.warning(f"Audio duration is very short: {duration:.2f}s")
        
        # Check for silence
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude < 0.001:
            logger.warning("Audio appears to be silent")
        
        # Check for clipping
        clipped_samples = np.sum(np.abs(audio_data) > 0.99)
        if clipped_samples > 0:
            logger.warning(f"Found {clipped_samples} clipped samples")
        
        logger.info("✅ Remix validation completed")
        logger.info(f"Duration: {duration:.2f}s, Max amplitude: {max_amplitude:.3f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Remix validation failed: {e}")
        return False


def analyze_audio_levels(audio_file):
    """
    Analyze audio levels and provide statistics
    
    Args:
        audio_file (Path): Path to audio file
    """
    try:
        audio_data, sample_rate = sf.read(audio_file)
        
        # Ensure mono
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Calculate statistics
        duration = len(audio_data) / sample_rate
        max_amplitude = np.max(np.abs(audio_data))
        rms_amplitude = np.sqrt(np.mean(audio_data**2))
        
        # Calculate dynamic range
        dynamic_range = 20 * np.log10(max_amplitude / (rms_amplitude + 1e-10))
        
        logger.info(f"Audio Analysis for {audio_file.name}:")
        logger.info(f"  Duration: {duration:.2f}s")
        logger.info(f"  Max amplitude: {max_amplitude:.3f}")
        logger.info(f"  RMS amplitude: {rms_amplitude:.3f}")
        logger.info(f"  Dynamic range: {dynamic_range:.1f} dB")
        
    except Exception as e:
        logger.error(f"Audio analysis failed: {e}")


if __name__ == "__main__":
    # Test the module
    import sys
    
    if len(sys.argv) != 6:
        print("Usage: python remix.py <original.wav> <dialogue.wav> <dubbing.wav> <output_m_e.wav> <output_mix.wav>")
        sys.exit(1)
    
    original_file = sys.argv[1]
    dialogue_file = sys.argv[2]
    dubbing_file = sys.argv[3]
    m_e_bed_file = sys.argv[4]
    mix_file = sys.argv[5]
    
    logging.basicConfig(level=logging.INFO)
    
    if not check_ffmpeg():
        logger.warning("FFmpeg not found - using manual audio processing")
    
    try:
        run(original_file, dialogue_file, dubbing_file, m_e_bed_file, mix_file)
        
        # Analyze output
        logger.info("Analyzing output audio...")
        analyze_audio_levels(Path(mix_file))
        
        # Validate output
        if validate_remix(mix_file):
            print("✅ Audio remixing completed successfully")
        else:
            print("⚠️ Audio remixing completed but validation failed")
            
    except Exception as e:
        logger.error(f"❌ Audio remixing failed: {e}")
        sys.exit(1) 