"""
Speech Synthesis Module
Uses ElevenLabs API to synthesize Arabic speech with character-specific voices
"""

import logging
import pandas as pd
import numpy as np
import soundfile as sf
from pathlib import Path
import io
import time
from elevenlabs import ElevenLabs, VoiceSettings

logger = logging.getLogger(__name__)


def run(input_csv, output_wav):
    """
    Synthesize Arabic speech from translated transcript
    
    Args:
        input_csv (Path): Path to input CSV file with Arabic translations
        output_wav (Path): Path to output WAV file
    """
    input_csv = Path(input_csv)
    output_wav = Path(output_wav)
    
    if not input_csv.exists():
        raise FileNotFoundError(f"Input file not found: {input_csv}")
    
    # Create output directory if it doesn't exist
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    
    # Import config here to avoid circular imports
    from config import (
        ELEVENLABS_API_KEY, ELEVENLABS_MODEL, CHARACTER_VOICES,
        VOICE_STABILITY, VOICE_SIMILARITY, VOICE_STYLE, VOICE_BOOST,
        SAMPLE_RATE
    )
    
    if ELEVENLABS_API_KEY == "your-elevenlabs-key-here":
        logger.error("ElevenLabs API key not set")
        raise ValueError("ElevenLabs API key not configured")
    
    # Initialize ElevenLabs client
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
    # Load transcript
    logger.info(f"Loading transcript from: {input_csv}")
    df = pd.read_csv(input_csv)
    
    required_columns = ['start_sec', 'end_sec', 'speaker', 'text_ar']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Missing required columns: {required_columns}")
    
    logger.info(f"Found {len(df)} segments to synthesize")
    
    # Calculate total duration
    total_duration = df['end_sec'].max()
    output_samples = int(total_duration * SAMPLE_RATE)
    output_audio = np.zeros(output_samples, dtype=np.float32)
    
    logger.info(f"Total duration: {total_duration:.2f} seconds")
    logger.info(f"Output array size: {output_samples} samples")
    
    # Voice settings
    voice_settings = VoiceSettings(
        stability=VOICE_STABILITY,
        similarity_boost=VOICE_SIMILARITY,
        style=VOICE_STYLE,
        use_speaker_boost=VOICE_BOOST
    )
    
    successful_syntheses = 0
    
    for index, row in df.iterrows():
        try:
            # Skip empty translations or errors
            if pd.isna(row['text_ar']) or 'TRANSLATION ERROR' in str(row['text_ar']):
                logger.warning(f"Skipping segment {index + 1} due to translation error")
                continue
                
            # Get voice ID for speaker
            speaker = row['speaker']
            voice_id = CHARACTER_VOICES.get(speaker, CHARACTER_VOICES['default'])
            
            # Calculate timing
            start_time = float(row['start_sec'])
            end_time = float(row['end_sec'])
            duration = end_time - start_time
            
            logger.info(f"Synthesizing segment {index + 1}/{len(df)}: {row['text_ar'][:50]}...")
            logger.info(f"Speaker: {speaker}, Voice: {voice_id}, Duration: {duration:.1f}s")
            
            # Generate speech using the correct ElevenLabs API
            audio_generator = client.text_to_speech.convert(
                voice_id=voice_id,
                text=row['text_ar'],
                model_id=ELEVENLABS_MODEL,
                voice_settings=voice_settings
            )
            
            # Convert generator to bytes
            audio_bytes = b''.join(audio_generator)
            
            # Load audio data
            audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype='float32')
            
            # Handle mono/stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)  # Convert to mono
            
            # Resample if necessary
            if sample_rate != SAMPLE_RATE:
                logger.warning(f"Resampling from {sample_rate} to {SAMPLE_RATE}")
                from scipy.signal import resample
                num_samples = int(len(audio_data) * SAMPLE_RATE / sample_rate)
                audio_data = resample(audio_data, num_samples)
            
            # Calculate placement in output array
            start_sample = int(start_time * SAMPLE_RATE)
            audio_length = len(audio_data)
            end_sample = start_sample + audio_length
            
            # Ensure we don't exceed output array bounds
            if end_sample > len(output_audio):
                logger.warning(f"Audio segment extends beyond total duration, truncating")
                audio_data = audio_data[:len(output_audio) - start_sample]
                end_sample = len(output_audio)
            
            # Add to output audio
            output_audio[start_sample:end_sample] += audio_data
            
            successful_syntheses += 1
            logger.info(f"✅ Synthesized segment {index + 1}")
            
            # Rate limiting - be respectful to ElevenLabs API
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Failed to synthesize segment {index + 1}: {e}")
            continue
    
    # Normalize audio to prevent clipping
    max_val = np.max(np.abs(output_audio))
    if max_val > 0:
        output_audio = output_audio / max_val * 0.95
    
    # Save output
    sf.write(output_wav, output_audio, SAMPLE_RATE)
    
    logger.info(f"✅ Speech synthesis completed and saved to: {output_wav}")
    logger.info(f"Successfully synthesized: {successful_syntheses}/{len(df)} segments")
    
    # Log file statistics
    file_size = output_wav.stat().st_size / (1024*1024)
    logger.info(f"Output file size: {file_size:.2f} MB")
    
    if successful_syntheses < len(df):
        logger.warning(f"Failed to synthesize {len(df) - successful_syntheses} segments")


def check_elevenlabs_api():
    """Check if ElevenLabs API is available and configured"""
    try:
        from config import ELEVENLABS_API_KEY
        
        if ELEVENLABS_API_KEY == "your-elevenlabs-key-here":
            return False
        
        # Test API connection
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        # Test with a simple generation
        test_audio_generator = client.text_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            text="Hello",
            model_id="eleven_multilingual_v2"
        )
        
        # Convert generator to bytes to test
        test_audio_bytes = b''.join(test_audio_generator)
        
        return True
        
    except Exception as e:
        logger.error(f"ElevenLabs API check failed: {e}")
        return False


def list_available_voices():
    """List available voices from ElevenLabs"""
    try:
        from config import ELEVENLABS_API_KEY
        
        if ELEVENLABS_API_KEY == "your-elevenlabs-key-here":
            logger.error("ElevenLabs API key not set")
            return
        
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        voices = client.voices.get_all()
        
        logger.info("Available ElevenLabs voices:")
        logger.info("=" * 40)
        
        for voice in voices.voices:
            logger.info(f"Name: {voice.name}")
            logger.info(f"ID: {voice.voice_id}")
            logger.info(f"Category: {voice.category}")
            logger.info(f"Description: {voice.description}")
            logger.info("-" * 40)
            
    except Exception as e:
        logger.error(f"Failed to list voices: {e}")


def validate_synthesis(wav_path):
    """
    Validate the generated speech audio file
    
    Args:
        wav_path (Path): Path to WAV file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        wav_path = Path(wav_path)
        
        if not wav_path.exists():
            logger.error(f"Output file not found: {wav_path}")
            return False
        
        # Check file size
        file_size = wav_path.stat().st_size
        if file_size == 0:
            logger.error("Output file is empty")
            return False
        
        # Load and check audio
        audio_data, sample_rate = sf.read(wav_path)
        
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
        
        logger.info("✅ Audio validation completed")
        logger.info(f"Duration: {duration:.2f}s, Max amplitude: {max_amplitude:.3f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Audio validation failed: {e}")
        return False


def test_voice_synthesis(text="مرحبا، هذا اختبار للصوت", voice_id=None):
    """
    Test voice synthesis with a simple Arabic phrase
    
    Args:
        text (str): Arabic text to synthesize
        voice_id (str): Voice ID to use (optional)
    """
    try:
        from config import ELEVENLABS_API_KEY, CHARACTER_VOICES
        
        if ELEVENLABS_API_KEY == "your-elevenlabs-key-here":
            logger.error("ElevenLabs API key not set")
            return
        
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        # Use default voice if none specified
        if voice_id is None:
            voice_id = CHARACTER_VOICES['default']
        
        logger.info(f"Testing voice synthesis with voice ID: {voice_id}")
        logger.info(f"Text: {text}")
        
        # Generate speech
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2"
        )
        
        # Convert generator to bytes
        audio_bytes = b''.join(audio_generator)
        
        # Save test file
        test_file = Path("output/voice_test.wav")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(test_file, 'wb') as f:
            f.write(audio_bytes)
        
        logger.info(f"✅ Voice test completed, saved to: {test_file}")
        
    except Exception as e:
        logger.error(f"Voice test failed: {e}")


if __name__ == "__main__":
    # Test the module
    import sys
    
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python synthesize.py <input.csv> <output.wav>  - Synthesize speech")
        print("  python synthesize.py --list-voices             - List available voices")
        print("  python synthesize.py --test-voice [voice_id]   - Test voice synthesis")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)
    
    if sys.argv[1] == "--list-voices":
        list_available_voices()
    elif sys.argv[1] == "--test-voice":
        voice_id = sys.argv[2] if len(sys.argv) > 2 else None
        test_voice_synthesis(voice_id=voice_id)
    elif len(sys.argv) == 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        
        if not check_elevenlabs_api():
            logger.error("ElevenLabs API not available or not configured")
            sys.exit(1)
        
        try:
            run(input_file, output_file)
            
            # Validate output
            if validate_synthesis(output_file):
                print("✅ Speech synthesis completed successfully")
            else:
                print("⚠️ Speech synthesis completed but validation failed")
                
        except Exception as e:
            logger.error(f"❌ Speech synthesis failed: {e}")
            sys.exit(1)
    else:
        print("Invalid arguments")
        sys.exit(1) 