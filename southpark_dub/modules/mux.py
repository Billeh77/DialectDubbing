"""
Video Muxing Module
Combines the mixed audio with the original video to create the final dubbed MP4
"""

import logging
import subprocess
from pathlib import Path
import os

logger = logging.getLogger(__name__)


def run(input_video, input_audio, output_video):
    """
    Mux new audio with original video to create final dubbed MP4
    
    Args:
        input_video (Path): Path to original MP4 video
        input_audio (Path): Path to mixed audio WAV file
        output_video (Path): Path to output dubbed MP4 file
    """
    input_video = Path(input_video)
    input_audio = Path(input_audio)
    output_video = Path(output_video)
    
    # Check input files exist
    if not input_video.exists():
        raise FileNotFoundError(f"Input video not found: {input_video}")
    if not input_audio.exists():
        raise FileNotFoundError(f"Input audio not found: {input_audio}")
    
    # Create output directory
    output_video.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"📼 Muxing video {input_video} with audio {input_audio}")
    
    try:
        # Method 1: Use FFmpeg for muxing
        mux_with_ffmpeg(input_video, input_audio, output_video)
        
    except Exception as e:
        logger.error(f"FFmpeg muxing failed: {e}")
        
        # Method 2: Fallback to moviepy
        try:
            logger.info("Falling back to moviepy for muxing...")
            mux_with_moviepy(input_video, input_audio, output_video)
        except Exception as e2:
            logger.error(f"MoviePy muxing also failed: {e2}")
            raise RuntimeError(f"All muxing methods failed. FFmpeg: {e}, MoviePy: {e2}")


def mux_with_ffmpeg(input_video, input_audio, output_video):
    """
    Mux video and audio using FFmpeg
    
    Args:
        input_video (Path): Path to input video
        input_audio (Path): Path to input audio
        output_video (Path): Path to output video
    """
    # FFmpeg command for muxing
    # -i: input files
    # -map 0:v: map video from first input
    # -map 1:a: map audio from second input
    # -c:v copy: copy video codec (no re-encoding)
    # -c:a aac: encode audio as AAC
    # -b:a 192k: audio bitrate
    # -shortest: finish encoding when shortest input ends
    # -y: overwrite output file
    
    cmd = [
        "ffmpeg",
        "-i", str(input_video),
        "-i", str(input_audio),
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-y", str(output_video)
    ]
    
    logger.info("Using FFmpeg for video muxing...")
    logger.debug(f"FFmpeg command: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )
    
    if result.returncode == 0:
        logger.info("✅ Video muxing completed using FFmpeg")
    else:
        raise RuntimeError(f"FFmpeg failed with return code {result.returncode}")


def mux_with_moviepy(input_video, input_audio, output_video):
    """
    Mux video and audio using MoviePy as fallback
    
    Args:
        input_video (Path): Path to input video
        input_audio (Path): Path to input audio
        output_video (Path): Path to output video
    """
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
        
        logger.info("Using MoviePy for video muxing...")
        
        # Load video and audio
        video = VideoFileClip(str(input_video))
        audio = AudioFileClip(str(input_audio))
        
        # Set audio to video
        final_video = video.set_audio(audio)
        
        # Write the result
        final_video.write_videofile(
            str(output_video),
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Clean up
        video.close()
        audio.close()
        final_video.close()
        
        logger.info("✅ Video muxing completed using MoviePy")
        
    except ImportError:
        raise RuntimeError("MoviePy not available for fallback muxing")
    except Exception as e:
        raise RuntimeError(f"MoviePy muxing failed: {e}")


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


def check_moviepy():
    """Check if MoviePy is available"""
    try:
        import moviepy
        return True
    except ImportError:
        return False


def validate_output_video(video_path):
    """
    Validate the output video file
    
    Args:
        video_path (Path): Path to output video
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        video_path = Path(video_path)
        
        if not video_path.exists():
            logger.error(f"Output video not found: {video_path}")
            return False
        
        # Check file size
        file_size = video_path.stat().st_size
        if file_size == 0:
            logger.error("Output video file is empty")
            return False
        
        # Use FFprobe to check video properties
        if check_ffmpeg():
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(video_path)
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if result.returncode == 0:
                    import json
                    info = json.loads(result.stdout)
                    
                    # Check for video and audio streams
                    video_streams = [s for s in info['streams'] if s['codec_type'] == 'video']
                    audio_streams = [s for s in info['streams'] if s['codec_type'] == 'audio']
                    
                    if not video_streams:
                        logger.error("No video streams found")
                        return False
                    
                    if not audio_streams:
                        logger.error("No audio streams found")
                        return False
                    
                    # Log video info
                    video_stream = video_streams[0]
                    audio_stream = audio_streams[0]
                    
                    duration = float(info['format']['duration'])
                    
                    logger.info("✅ Video validation completed")
                    logger.info(f"Duration: {duration:.2f}s")
                    logger.info(f"Video: {video_stream['codec_name']} {video_stream['width']}x{video_stream['height']}")
                    logger.info(f"Audio: {audio_stream['codec_name']} {audio_stream['sample_rate']}Hz")
                    
                    return True
                    
            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                logger.warning(f"FFprobe validation failed: {e}")
        
        # Basic file size check if FFprobe fails
        file_size_mb = file_size / (1024 * 1024)
        logger.info(f"Output video file size: {file_size_mb:.2f} MB")
        
        if file_size_mb > 1.0:  # Reasonable minimum size
            logger.info("✅ Basic video validation passed")
            return True
        else:
            logger.warning("Output video file seems too small")
            return False
            
    except Exception as e:
        logger.error(f"Video validation failed: {e}")
        return False


def get_video_info(video_path):
    """
    Get detailed information about a video file
    
    Args:
        video_path (Path): Path to video file
        
    Returns:
        dict: Video information or None if failed
    """
    try:
        if not check_ffmpeg():
            logger.warning("FFmpeg not available for video info")
            return None
        
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
        
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return None


def compare_videos(original_video, dubbed_video):
    """
    Compare original and dubbed videos
    
    Args:
        original_video (Path): Path to original video
        dubbed_video (Path): Path to dubbed video
    """
    try:
        logger.info("Comparing original and dubbed videos...")
        
        orig_info = get_video_info(original_video)
        dub_info = get_video_info(dubbed_video)
        
        if orig_info and dub_info:
            # Compare durations
            orig_duration = float(orig_info['format']['duration'])
            dub_duration = float(dub_info['format']['duration'])
            
            duration_diff = abs(orig_duration - dub_duration)
            
            logger.info(f"Original duration: {orig_duration:.2f}s")
            logger.info(f"Dubbed duration: {dub_duration:.2f}s")
            logger.info(f"Duration difference: {duration_diff:.2f}s")
            
            if duration_diff > 1.0:
                logger.warning("Significant duration difference detected")
            
            # Compare video properties
            orig_video_stream = [s for s in orig_info['streams'] if s['codec_type'] == 'video'][0]
            dub_video_stream = [s for s in dub_info['streams'] if s['codec_type'] == 'video'][0]
            
            if (orig_video_stream['width'] != dub_video_stream['width'] or
                orig_video_stream['height'] != dub_video_stream['height']):
                logger.warning("Video resolution mismatch")
            
            logger.info("✅ Video comparison completed")
        else:
            logger.warning("Could not compare videos - missing information")
            
    except Exception as e:
        logger.error(f"Video comparison failed: {e}")


if __name__ == "__main__":
    # Test the module
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python mux.py <input_video.mp4> <input_audio.wav> <output_video.mp4>")
        sys.exit(1)
    
    input_video_file = sys.argv[1]
    input_audio_file = sys.argv[2]
    output_video_file = sys.argv[3]
    
    logging.basicConfig(level=logging.INFO)
    
    # Check available tools
    has_ffmpeg = check_ffmpeg()
    has_moviepy = check_moviepy()
    
    if not has_ffmpeg and not has_moviepy:
        logger.error("Neither FFmpeg nor MoviePy available for muxing")
        sys.exit(1)
    
    if not has_ffmpeg:
        logger.warning("FFmpeg not available - using MoviePy only")
    
    try:
        run(input_video_file, input_audio_file, output_video_file)
        
        # Validate output
        if validate_output_video(output_video_file):
            print("✅ Video muxing completed successfully")
            
            # Compare with original
            compare_videos(Path(input_video_file), Path(output_video_file))
        else:
            print("⚠️ Video muxing completed but validation failed")
            
    except Exception as e:
        logger.error(f"❌ Video muxing failed: {e}")
        sys.exit(1) 