#!/usr/bin/env python3
"""
Simple FFmpeg downloader for PyInstaller bundling
"""

import urllib.request
import zipfile
import shutil
from pathlib import Path

def download_ffmpeg():
    """Download FFmpeg essentials for Windows"""
    print("🔽 Downloading FFmpeg...")
    
    # FFmpeg download URL (Windows essentials build)
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_file = "ffmpeg.zip"
    
    try:
        # Download
        print("   Downloading from gyan.dev...")
        urllib.request.urlretrieve(url, zip_file)
        
        # Extract
        print("   Extracting...")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall("temp_ffmpeg")
        
        # Find the extracted folder
        temp_dir = Path("temp_ffmpeg")
        extracted_folders = [d for d in temp_dir.iterdir() if d.is_dir()]
        
        if extracted_folders:
            ffmpeg_folder = extracted_folders[0] / "bin"
            
            # Copy executables to ffmpeg folder
            ffmpeg_dir = Path("ffmpeg")
            ffmpeg_dir.mkdir(exist_ok=True)
            
            for exe in ["ffmpeg.exe", "ffprobe.exe"]:
                src = ffmpeg_folder / exe
                dst = ffmpeg_dir / exe
                if src.exists():
                    shutil.copy2(src, dst)
                    print(f"   ✅ Copied {exe}")
        
        # Cleanup
        Path(zip_file).unlink(missing_ok=True)
        shutil.rmtree("temp_ffmpeg", ignore_errors=True)
        
        print("✅ FFmpeg download complete!")
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

if __name__ == "__main__":
    download_ffmpeg() 