#!/usr/bin/env python3
"""
Simple test script to verify the South Park AI Dubbing system setup
Tests basic functionality without requiring heavy ML dependencies
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_python_version():
    """Test Python version compatibility"""
    logger.info("Testing Python version...")
    
    version = sys.version_info
    logger.info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 8):
        logger.info("✅ Python version is compatible")
        return True
    else:
        logger.error("❌ Python 3.8+ required")
        return False

def test_virtual_environment():
    """Test if running in virtual environment"""
    logger.info("Testing virtual environment...")
    
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if in_venv:
        logger.info("✅ Running in virtual environment")
        return True
    else:
        logger.warning("⚠️ Not in virtual environment (recommended to use venv)")
        return False

def test_basic_imports():
    """Test basic Python imports"""
    logger.info("Testing basic imports...")
    
    try:
        import pathlib
        import logging
        import subprocess
        import json
        import os
        logger.info("✅ Basic imports successful")
        return True
    except ImportError as e:
        logger.error(f"❌ Basic import failed: {e}")
        return False

def test_config_import():
    """Test config module import"""
    logger.info("Testing config import...")
    
    try:
        from config import ASSETS_DIR, OUTPUT_DIR, INPUT_MP4
        logger.info("✅ Config import successful")
        return True
    except ImportError as e:
        logger.error(f"❌ Config import failed: {e}")
        return False

def test_directory_structure():
    """Test project directory structure"""
    logger.info("Testing directory structure...")
    
    expected_dirs = [
        Path("assets"),
        Path("output"),
        Path("modules"),
        Path("interface")
    ]
    
    expected_files = [
        Path("config.py"),
        Path("main.py"),
        Path("requirements.txt"),
        Path("README.md")
    ]
    
    all_good = True
    
    for dir_path in expected_dirs:
        if dir_path.exists():
            logger.info(f"✅ {dir_path} exists")
        else:
            logger.error(f"❌ {dir_path} missing")
            all_good = False
    
    for file_path in expected_files:
        if file_path.exists():
            logger.info(f"✅ {file_path} exists")
        else:
            logger.error(f"❌ {file_path} missing")
            all_good = False
    
    return all_good

def test_module_structure():
    """Test module files exist"""
    logger.info("Testing module structure...")
    
    module_files = [
        Path("modules/__init__.py"),
        Path("modules/extract_audio.py"),
        Path("modules/isolate_dialogue.py"),
        Path("modules/transcribe.py"),
        Path("modules/translate.py"),
        Path("modules/synthesize.py"),
        Path("modules/remix.py"),
        Path("modules/mux.py")
    ]
    
    all_good = True
    
    for file_path in module_files:
        if file_path.exists():
            logger.info(f"✅ {file_path} exists")
        else:
            logger.error(f"❌ {file_path} missing")
            all_good = False
    
    return all_good

def test_output_directories():
    """Test output directories can be created"""
    logger.info("Testing output directory creation...")
    
    try:
        from config import OUTPUT_DIR, ASSETS_DIR
        
        # Create directories
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        
        if OUTPUT_DIR.exists() and ASSETS_DIR.exists():
            logger.info("✅ Output directories created successfully")
            return True
        else:
            logger.error("❌ Failed to create output directories")
            return False
            
    except Exception as e:
        logger.error(f"❌ Directory creation failed: {e}")
        return False

def test_ffmpeg_availability():
    """Test if FFmpeg is available"""
    logger.info("Testing FFmpeg availability...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("✅ FFmpeg is available")
            return True
        else:
            logger.warning("⚠️ FFmpeg not available")
            return False
            
    except FileNotFoundError:
        logger.warning("⚠️ FFmpeg not found in PATH")
        return False
    except Exception as e:
        logger.error(f"❌ FFmpeg test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    logger.info("🧪 Starting South Park AI Dubbing System Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Python Version", test_python_version),
        ("Virtual Environment", test_virtual_environment),
        ("Basic Imports", test_basic_imports),
        ("Config Import", test_config_import),
        ("Directory Structure", test_directory_structure),
        ("Module Structure", test_module_structure),
        ("Output Directories", test_output_directories),
        ("FFmpeg Availability", test_ffmpeg_availability)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\nPassed: {passed}/{total} tests")
    
    if passed == total:
        logger.info("🎉 All tests passed! System is ready.")
        return True
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        logger.info("\n🚀 Next steps:")
        logger.info("1. Install dependencies: pip install -r requirements.txt")
        logger.info("2. Set up API keys in config.py")
        logger.info("3. Upload a video: python interface/upload_interface.py upload video.mp4")
        logger.info("4. Run the pipeline: python main.py")
        sys.exit(0)
    else:
        logger.error("\n❌ System setup incomplete. Fix the issues above.")
        sys.exit(1) 