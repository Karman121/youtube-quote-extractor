"""
Runtime hook for YouTube Quote Extractor
This hook sets up the environment when the executable starts
"""

import os
import sys
from pathlib import Path


def setup_bundled_resources():
    """Set up bundled resources (ffmpeg, .env) when running as executable"""
    
    # Determine if we're running as a PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller executable
        bundle_dir = Path(sys._MEIPASS)
        
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
        
        # Load .env file if bundled
        env_file = bundle_dir / '.env'
        if env_file.exists():
            # Load environment variables from bundled .env file
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
            except Exception as e:
                print(f"Warning: Could not load bundled .env file: {e}")
    
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