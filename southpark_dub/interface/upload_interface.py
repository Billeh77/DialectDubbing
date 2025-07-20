#!/usr/bin/env python3
"""
Upload Interface for South Park AI Dubbing System
Provides both CLI and optional Gradio web interface for uploading and processing videos
"""

import argparse
import logging
import sys
from pathlib import Path
import shutil
import tempfile
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import *
from main import run_pipeline


def cli_interface():
    """Command-line interface for the dubbing system"""
    parser = argparse.ArgumentParser(
        description="South Park AI Dubbing System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python upload_interface.py upload video.mp4
  python upload_interface.py process
  python upload_interface.py status
  python upload_interface.py web
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload a video file')
    upload_parser.add_argument('video_file', help='Path to MP4 video file')
    upload_parser.add_argument('--copy', action='store_true', help='Copy file instead of moving')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process the uploaded video')
    process_parser.add_argument('--video', help='Specific video file to process')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Web interface command
    web_parser = subparsers.add_parser('web', help='Launch web interface')
    web_parser.add_argument('--port', type=int, default=7860, help='Port for web interface')
    web_parser.add_argument('--host', default='localhost', help='Host for web interface')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup and check dependencies')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test individual modules')
    test_parser.add_argument('module', choices=['extract', 'isolate', 'transcribe', 'translate', 'synthesize', 'remix', 'mux'], help='Module to test')
    
    args = parser.parse_args()
    
    if args.command == 'upload':
        upload_video(args.video_file, copy_file=args.copy)
    elif args.command == 'process':
        process_video(args.video)
    elif args.command == 'status':
        show_status()
    elif args.command == 'web':
        launch_web_interface(args.host, args.port)
    elif args.command == 'setup':
        setup_system()
    elif args.command == 'test':
        test_module(args.module)
    else:
        parser.print_help()


def upload_video(video_file, copy_file=False):
    """Upload a video file to the assets directory"""
    video_path = Path(video_file)
    
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return False
    
    # Check if it's a video file
    if not video_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
        logger.error(f"Unsupported video format: {video_path.suffix}")
        return False
    
    # Create assets directory if it doesn't exist
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Determine destination
    dest_path = ASSETS_DIR / "Southpark_short_clip.mp4"
    
    try:
        if copy_file:
            shutil.copy2(video_path, dest_path)
            logger.info(f"✅ Video copied to: {dest_path}")
        else:
            shutil.move(str(video_path), dest_path)
            logger.info(f"✅ Video moved to: {dest_path}")
        
        # Show file info
        file_size = dest_path.stat().st_size / (1024 * 1024)
        logger.info(f"File size: {file_size:.2f} MB")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to upload video: {e}")
        return False


def process_video(video_file=None):
    """Process the uploaded video through the dubbing pipeline"""
    if video_file:
        video_path = Path(video_file)
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return False
        
        # Copy to assets directory
        upload_video(video_file, copy_file=True)
    
    # Check if input video exists
    if not INPUT_MP4.exists():
        logger.error(f"No video file found at: {INPUT_MP4}")
        logger.info("Please upload a video first using: python upload_interface.py upload <video_file>")
        return False
    
    # Run the pipeline
    logger.info("🚀 Starting dubbing pipeline...")
    
    try:
        # Import and run the main pipeline
        success = run_pipeline()
        
        if success:
            logger.info("✅ Dubbing pipeline completed successfully!")
            
            # Show output files
            logger.info("\n📁 Generated files:")
            for file_path in [TRANSCRIPT_CSV, TRANSCRIPT_AR_CSV, DUBBING_AR_WAV, FINAL_MP4]:
                if file_path.exists():
                    size = file_path.stat().st_size / (1024 * 1024)
                    logger.info(f"  {file_path.name}: {size:.2f} MB")
            
            return True
        else:
            logger.error("❌ Dubbing pipeline failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pipeline error: {e}")
        return False


def show_status():
    """Show system status and configuration"""
    logger.info("🔍 South Park AI Dubbing System Status")
    logger.info("=" * 50)
    
    # Check input file
    if INPUT_MP4.exists():
        size = INPUT_MP4.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Input video: {INPUT_MP4.name} ({size:.2f} MB)")
    else:
        logger.info("❌ No input video found")
    
    # Check dependencies
    logger.info("\n🔧 Dependencies:")
    
    # Check FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        logger.info("✅ FFmpeg")
    except:
        logger.info("❌ FFmpeg")
    
    # Check Python modules
    modules = [
        ('torch', 'PyTorch'),
        ('whisperx', 'WhisperX'),
        ('demucs', 'Demucs'),
        ('openai', 'OpenAI'),
        ('elevenlabs', 'ElevenLabs'),
        ('moviepy', 'MoviePy'),
        ('gradio', 'Gradio')
    ]
    
    for module, name in modules:
        try:
            __import__(module)
            logger.info(f"✅ {name}")
        except ImportError:
            logger.info(f"❌ {name}")
    
    # Check API keys
    logger.info("\n🔑 API Keys:")
    api_keys = [
        (OPENAI_API_KEY, "OpenAI"),
        (ELEVENLABS_API_KEY, "ElevenLabs"),
        (HF_TOKEN, "HuggingFace")
    ]
    
    for key, name in api_keys:
        if key and key != f"your-{name.lower()}-key-here":
            logger.info(f"✅ {name}")
        else:
            logger.info(f"❌ {name}")
    
    # Check output files
    logger.info("\n📁 Output Files:")
    output_files = [
        (AUDIO_RAW, "Raw audio"),
        (AUDIO_DIALOGUE, "Dialogue audio"),
        (TRANSCRIPT_CSV, "Transcript"),
        (TRANSCRIPT_AR_CSV, "Arabic transcript"),
        (DUBBING_AR_WAV, "Arabic dubbing"),
        (FINAL_MP4, "Final video")
    ]
    
    for file_path, desc in output_files:
        if file_path.exists():
            size = file_path.stat().st_size / (1024 * 1024)
            logger.info(f"✅ {desc}: {size:.2f} MB")
        else:
            logger.info(f"❌ {desc}")


def setup_system():
    """Setup and check system dependencies"""
    logger.info("🔧 Setting up South Park AI Dubbing System")
    logger.info("=" * 50)
    
    # Create directories
    logger.info("Creating directories...")
    for dir_path in [ASSETS_DIR, OUTPUT_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ {dir_path}")
    
    # Check Python version
    import sys
    python_version = sys.version_info
    logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        logger.error("❌ Python 3.8+ required")
        return False
    
    # Check virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        logger.info("✅ Virtual environment detected")
    else:
        logger.warning("⚠️ Not in a virtual environment")
    
    # Show next steps
    logger.info("\n📋 Next steps:")
    logger.info("1. Install dependencies: pip install -r requirements.txt")
    logger.info("2. Set API keys in config.py or environment variables")
    logger.info("3. Upload a video: python upload_interface.py upload video.mp4")
    logger.info("4. Process video: python upload_interface.py process")
    
    return True


def test_module(module_name):
    """Test individual modules"""
    logger.info(f"🧪 Testing {module_name} module")
    
    # Create test files if needed
    test_dir = OUTPUT_DIR / "test"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        if module_name == 'extract':
            from modules.extract_audio import check_ffmpeg
            if check_ffmpeg():
                logger.info("✅ FFmpeg available for audio extraction")
            else:
                logger.error("❌ FFmpeg not available")
        
        elif module_name == 'isolate':
            from modules.isolate_dialogue import check_demucs
            if check_demucs():
                logger.info("✅ Demucs available for dialogue isolation")
            else:
                logger.error("❌ Demucs not available")
        
        elif module_name == 'transcribe':
            from modules.transcribe import check_whisperx, check_pyannote
            if check_whisperx():
                logger.info("✅ WhisperX available")
            else:
                logger.error("❌ WhisperX not available")
            
            if check_pyannote():
                logger.info("✅ PyAnnote available")
            else:
                logger.error("❌ PyAnnote not available")
        
        elif module_name == 'translate':
            from modules.translate import check_openai_api
            if check_openai_api():
                logger.info("✅ OpenAI API available")
            else:
                logger.error("❌ OpenAI API not available")
        
        elif module_name == 'synthesize':
            from modules.synthesize import check_elevenlabs_api
            if check_elevenlabs_api():
                logger.info("✅ ElevenLabs API available")
            else:
                logger.error("❌ ElevenLabs API not available")
        
        elif module_name == 'remix':
            from modules.remix import check_ffmpeg
            if check_ffmpeg():
                logger.info("✅ FFmpeg available for remixing")
            else:
                logger.error("❌ FFmpeg not available")
        
        elif module_name == 'mux':
            from modules.mux import check_ffmpeg, check_moviepy
            if check_ffmpeg():
                logger.info("✅ FFmpeg available for muxing")
            elif check_moviepy():
                logger.info("✅ MoviePy available for muxing")
            else:
                logger.error("❌ No muxing tools available")
        
        logger.info(f"✅ {module_name} module test completed")
        
    except Exception as e:
        logger.error(f"❌ {module_name} module test failed: {e}")


def launch_web_interface(host='localhost', port=7860):
    """Launch Gradio web interface"""
    try:
        import gradio as gr
        
        logger.info(f"🌐 Launching web interface at http://{host}:{port}")
        
        def gradio_upload(video_file):
            if video_file is None:
                return "No file uploaded"
            
            try:
                # Copy uploaded file to assets directory
                dest_path = ASSETS_DIR / "Southpark_short_clip.mp4"
                shutil.copy2(video_file.name, dest_path)
                
                file_size = dest_path.stat().st_size / (1024 * 1024)
                return f"✅ Video uploaded successfully: {file_size:.2f} MB"
                
            except Exception as e:
                return f"❌ Upload failed: {str(e)}"
        
        def gradio_process():
            if not INPUT_MP4.exists():
                return "❌ No video file uploaded"
            
            try:
                success = run_pipeline()
                if success:
                    return "✅ Dubbing completed successfully!"
                else:
                    return "❌ Dubbing failed"
            except Exception as e:
                return f"❌ Processing error: {str(e)}"
        
        def gradio_download():
            if FINAL_MP4.exists():
                return str(FINAL_MP4)
            else:
                return None
        
        # Create Gradio interface
        with gr.Blocks(title="South Park AI Dubbing") as demo:
            gr.Markdown("# 🎬 South Park AI Dubbing System")
            gr.Markdown("Upload a South Park episode and get it dubbed in Lebanese Arabic!")
            
            with gr.Row():
                with gr.Column():
                    video_input = gr.File(
                        file_types=['.mp4', '.avi', '.mov', '.mkv'],
                        label="Upload Video File"
                    )
                    upload_btn = gr.Button("📤 Upload Video", variant="primary")
                    upload_status = gr.Textbox(label="Upload Status", interactive=False)
                
                with gr.Column():
                    process_btn = gr.Button("🚀 Start Dubbing", variant="secondary")
                    process_status = gr.Textbox(label="Processing Status", interactive=False)
                    download_btn = gr.Button("📥 Download Result")
                    download_file = gr.File(label="Download Dubbed Video")
            
            # Event handlers
            upload_btn.click(
                gradio_upload,
                inputs=[video_input],
                outputs=[upload_status]
            )
            
            process_btn.click(
                gradio_process,
                outputs=[process_status]
            )
            
            download_btn.click(
                gradio_download,
                outputs=[download_file]
            )
        
        # Launch interface
        demo.launch(server_name=host, server_port=port, share=False)
        
    except ImportError:
        logger.error("❌ Gradio not installed. Install with: pip install gradio")
        return False
    except Exception as e:
        logger.error(f"❌ Web interface failed: {e}")
        return False


if __name__ == "__main__":
    cli_interface() 