# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Get the current directory
current_dir = Path.cwd()

# Define paths
ffmpeg_dir = current_dir / "ffmpeg"
env_file = current_dir / ".env"

# Collect data files
datas = []

# Add .env file if it exists
if env_file.exists():
    datas.append((str(env_file), '.'))
    print(f"✅ Found .env file: {env_file}")
else:
    print("⚠️  No .env file found. You may need to create one with your GEMINI_API_KEY")

# Add ffmpeg executables if they exist
ffmpeg_exe = ffmpeg_dir / "ffmpeg.exe"
ffprobe_exe = ffmpeg_dir / "ffprobe.exe"

if ffmpeg_exe.exists() and ffprobe_exe.exists():
    datas.append((str(ffmpeg_exe), 'ffmpeg'))
    datas.append((str(ffprobe_exe), 'ffmpeg'))
    print(f"✅ Found ffmpeg executables in: {ffmpeg_dir}")
else:
    print("⚠️  FFmpeg executables not found. Run download_ffmpeg.py first or install ffmpeg manually")

# Hidden imports for all dependencies
hiddenimports = [
    'yt_dlp',
    'google.generativeai',
    'dotenv',
    'tenacity',
    'pydub',
    'ratelimit',
    'grpcio',
    'pydantic',
    'pydantic_core',
    'streamlit',
    'streamlit.web.cli',
    'streamlit.runtime.scriptrunner.magic_funcs',
    'altair',
    'plotly',
    'PIL',
    'PIL.Image',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'google.auth',
    'google.oauth2',
    'google.protobuf',
    'concurrent.futures',
    'threading',
    'multiprocessing',
    'subprocess',
    'tempfile',
    'shutil',
    'json',
    'logging',
    'pathlib',
    'os',
    'sys',
    'time',
    'datetime',
    'typing',
    'functools',
    'itertools',
    'collections',
    're',
    'math',
    'base64',
    'hashlib',
    'uuid',
    'socket',
    'ssl',
    'http',
    'urllib',
    'email',
    'mimetypes',
    'webbrowser',
    'platform',
    'signal',
    'atexit'
]

# Analysis
a = Analysis(
    ['run.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(current_dir / 'runtime_hook.py')],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
        'IPython'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YouTube Quote Extractor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an icon file here if you have one
    version=None
) 