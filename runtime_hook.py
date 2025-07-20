"""
Runtime hook for YouTube Quote Extractor
This hook sets up the environment when the executable starts
"""

import os
import sys
from pathlib import Path


def setup_bundled_resources():
    """Set up bundled resources (ffmpeg) and .env when running as executable"""
    
    # Determine if we're running as a PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller executable
        bundle_dir = Path(sys._MEIPASS)
        executable_dir = Path(sys.executable).parent
        
        # Set up ffmpeg path
        ffmpeg_dir = bundle_dir / 'ffmpeg'
        if ffmpeg_dir.exists():
            # Add ffmpeg directory to PATH
            current_path = os.environ.get('PATH', '')
            if str(ffmpeg_dir) not in current_path:
                os.environ['PATH'] = str(ffmpeg_dir) + os.pathsep + current_path
            
            # Set FFMPEG_LOCATION environment variable
            ffmpeg_exe = ffmpeg_dir / 'ffmpeg.exe'
            if ffmpeg_exe.exists():
                os.environ['FFMPEG_LOCATION'] = str(ffmpeg_exe)
        
        # Load .env file - try bundled first, then external
        bundled_env = bundle_dir / '.env'
        external_env = executable_dir / '.env'
        
        env_loaded = False
        
        # Try bundled .env file first
        if bundled_env.exists():
            try:
                with open(bundled_env, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                print(f"✅ Loaded bundled .env file from: {bundled_env}")
                env_loaded = True
            except Exception as e:
                print(f"❌ Warning: Could not load bundled .env file: {e}")
        
        # Fallback to external .env file if bundled doesn't exist or failed
        if not env_loaded and external_env.exists():
            try:
                with open(external_env, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                print(f"✅ Loaded external .env file from: {external_env}")
                env_loaded = True
            except Exception as e:
                print(f"❌ Warning: Could not load external .env file: {e}")
        
        if not env_loaded:
            print("⚠️  No .env file found (checked bundled and external locations)")
            print("📝 Either bundle .env during build or create external .env "
                  "with GEMINI_API_KEY=your_api_key")
    
    else:
        # Running as script - normal behavior
        # Add local ffmpeg to path if it exists
        local_ffmpeg = Path('ffmpeg')
        if local_ffmpeg.exists():
            current_path = os.environ.get('PATH', '')
            if str(local_ffmpeg.absolute()) not in current_path:
                os.environ['PATH'] = str(local_ffmpeg.absolute()) + os.pathsep + current_path


# Run setup when this module is imported
setup_bundled_resources() 