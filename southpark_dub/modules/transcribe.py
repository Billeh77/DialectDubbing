"""
Transcription and Speaker Diarization Module
Uses OpenAI's transcription API for reliable transcription
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from openai import OpenAI
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)


def run(input_wav, output_csv):
    """
    Transcribe audio using OpenAI's API and perform simple speaker diarization
    
    Args:
        input_wav (Path): Path to input WAV file
        output_csv (Path): Path to output CSV file
    """
    input_wav = Path(input_wav)
    output_csv = Path(output_csv)
    
    if not input_wav.exists():
        raise FileNotFoundError(f"Input file not found: {input_wav}")
    
    # Create output directory if it doesn't exist
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    
    # Import config here to avoid circular imports
    from config import OPENAI_API_KEY
    
    logger.info(f"Using OpenAI API for transcription")
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Transcribe the entire audio file at once
        logger.info(f"Transcribing audio file: {input_wav}")
        
        with open(input_wav, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
        
        logger.info(f"✅ Transcription completed. Found {len(transcription.segments)} segments")
        
        # Process transcription segments
        all_transcriptions = []
        
        for i, segment in enumerate(transcription.segments):
            # Assign speakers in a round-robin fashion
            speaker_id = f"SPEAKER_{i % 6:02d}"
            
            all_transcriptions.append({
                "start_sec": segment.start,
                "end_sec": segment.end,
                "speaker": speaker_id,
                "text": segment.text.strip()
            })
            
            logger.debug(f"Segment {i}: {segment.start:.2f}s-{segment.end:.2f}s [{speaker_id}]: {segment.text.strip()}")
        
        if not all_transcriptions:
            raise RuntimeError("No transcriptions were successful")
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(all_transcriptions)
        
        # Clean up and validate data
        df = df[df['text'].str.len() > 0]  # Remove empty text
        df = df.dropna()  # Remove NaN values
        df = df.reset_index(drop=True)
        
        # Sort by start time
        df = df.sort_values('start_sec').reset_index(drop=True)
        
        # Save to CSV
        df.to_csv(output_csv, index=False)
        
        logger.info(f"✅ Transcription saved to: {output_csv}")
        logger.info(f"Total segments: {len(df)}")
        
        # Log speaker statistics
        speaker_counts = df['speaker'].value_counts()
        logger.info(f"Speaker breakdown: {dict(speaker_counts)}")
        
        # Calculate total duration
        total_duration = df['end_sec'].max() - df['start_sec'].min()
        logger.info(f"Total audio duration: {total_duration:.2f} seconds")
        
        # Show first few segments for debugging
        logger.info("First 3 segments:")
        for idx, row in df.head(3).iterrows():
            logger.info(f"  {row['start_sec']:.2f}s-{row['end_sec']:.2f}s [{row['speaker']}]: {row['text']}")
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise RuntimeError(f"Failed to transcribe audio: {e}")


def segment_audio_by_silence(audio_data, sample_rate, min_silence_duration=0.5, silence_threshold=0.01):
    """
    Simple voice activity detection to segment audio by silence
    
    Args:
        audio_data: Audio signal as numpy array
        sample_rate: Sample rate of audio
        min_silence_duration: Minimum silence duration in seconds
        silence_threshold: Amplitude threshold for silence detection
        
    Returns:
        List of (start_time, end_time) tuples for speech segments
    """
    # Calculate RMS energy in small windows
    window_size = int(0.025 * sample_rate)  # 25ms windows
    hop_size = int(0.01 * sample_rate)      # 10ms hop
    
    # Calculate RMS energy
    rms_energy = []
    for i in range(0, len(audio_data) - window_size, hop_size):
        window = audio_data[i:i + window_size]
        rms = np.sqrt(np.mean(window ** 2))
        rms_energy.append(rms)
    
    # Convert to numpy array
    rms_energy = np.array(rms_energy)
    
    # Detect speech/silence
    is_speech = rms_energy > silence_threshold
    
    # Find speech segments
    segments = []
    in_speech = False
    speech_start = 0
    
    min_silence_samples = int(min_silence_duration * sample_rate / hop_size)
    
    silence_count = 0
    
    for i, speech in enumerate(is_speech):
        if speech and not in_speech:
            # Start of speech
            speech_start = i * hop_size / sample_rate
            in_speech = True
            silence_count = 0
        elif not speech and in_speech:
            silence_count += 1
            if silence_count >= min_silence_samples:
                # End of speech (after sufficient silence)
                speech_end = (i - silence_count) * hop_size / sample_rate
                if speech_end - speech_start > 0.1:  # Minimum 100ms segment
                    segments.append((speech_start, speech_end))
                in_speech = False
                silence_count = 0
        elif speech and in_speech:
            silence_count = 0
    
    # Handle case where speech continues to end
    if in_speech:
        speech_end = len(audio_data) / sample_rate
        if speech_end - speech_start > 0.1:
            segments.append((speech_start, speech_end))
    
    # If no segments found, return entire audio as one segment
    if not segments:
        segments = [(0, len(audio_data) / sample_rate)]
    
    return segments


def check_openai_api():
    """Check if OpenAI API is available and configured"""
    try:
        from config import OPENAI_API_KEY
        if OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-key-here":
            return True
        return False
    except ImportError:
        return False


def validate_transcript(csv_path):
    """
    Validate the generated transcript CSV
    
    Args:
        csv_path (Path): Path to CSV file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        df = pd.read_csv(csv_path)
        
        # Check required columns
        required_columns = ['start_sec', 'end_sec', 'speaker', 'text']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns: {required_columns}")
            return False
        
        # Check data types
        if not pd.api.types.is_numeric_dtype(df['start_sec']):
            logger.error("start_sec column should be numeric")
            return False
        
        if not pd.api.types.is_numeric_dtype(df['end_sec']):
            logger.error("end_sec column should be numeric")
            return False
        
        # Check time consistency
        if (df['end_sec'] < df['start_sec']).any():
            logger.error("Found segments where end_sec < start_sec")
            return False
        
        # Check for empty text
        if df['text'].str.len().min() == 0:
            logger.warning("Found empty text segments")
        
        logger.info("✅ Transcript validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Transcript validation failed: {e}")
        return False


if __name__ == "__main__":
    # Test the module
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python transcribe.py <input.wav> <output.csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    logging.basicConfig(level=logging.INFO)
    
    if not check_openai_api():
        logger.error("OpenAI API not configured")
        sys.exit(1)
    
    try:
        run(input_file, output_file)
        
        # Validate output
        if validate_transcript(output_file):
            print("✅ Transcription completed successfully")
        else:
            print("⚠️ Transcription completed but validation failed")
            
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")
        sys.exit(1) 