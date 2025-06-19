# 📦 Export Guide: Creating an Executable

This guide will help you create a standalone executable file from your YouTube Quote Extractor that can be shared and run on other computers without requiring Python installation.

## 🎯 Method 1: PyInstaller (Recommended)

PyInstaller is the most popular tool for creating Python executables. It bundles your Python application with all dependencies into a single executable.

### Step 1: Install PyInstaller

```bash
pip install pyinstaller
```

### Step 2: Create the Executable

#### Option A: Single File Executable (Slower startup, easier to share)
```bash
pyinstaller --onefile --windowed --name "YouTube-Quote-Extractor" run.py
```

#### Option B: Directory Distribution (Faster startup, multiple files)
```bash
pyinstaller --windowed --name "YouTube-Quote-Extractor" run.py
```

### Step 3: Advanced PyInstaller Configuration

Create a `build_config.spec` file for more control:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.py', '.'),
        ('main.py', '.'),
        ('web_gui.py', '.'),
        ('transcript_utils.py', '.'),
        ('audio_utils.py', '.'),
        ('quote_extraction.py', '.'),
        ('utils.py', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'google.generativeai',
        'whisperx',
        'yt_dlp',
        'pydub',
        'torch',
        'transformers',
        'numpy',
        'pandas',
        'scipy',
        'sklearn',
        'nltk',
        'pyannote.audio',
        'lightning',
        'tensorboardx',
        'asteroid_filterbanks',
        'speechbrain',
        'faster_whisper',
        'ctranslate2',
        'onnxruntime',
        'tokenizers',
        'huggingface_hub',
        'safetensors',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YouTube-Quote-Extractor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'  # Add an icon file if you have one
)
```

Then build with:
```bash
pyinstaller build_config.spec
```

## 🎯 Method 2: Auto-py-to-exe (GUI Tool)

This provides a graphical interface for PyInstaller.

### Step 1: Install Auto-py-to-exe
```bash
pip install auto-py-to-exe
```

### Step 2: Launch the GUI
```bash
auto-py-to-exe
```

### Step 3: Configure Settings
- **Script Location**: Select `run.py`
- **Onefile**: Choose "One File" for single executable
- **Console Window**: Choose "Window Based" to hide console
- **Additional Files**: Add all your Python files
- **Hidden Imports**: Add the packages listed in the spec file above

## 🎯 Method 3: cx_Freeze (Cross-platform)

### Step 1: Install cx_Freeze
```bash
pip install cx_freeze
```

### Step 2: Create setup.py
```python
import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but some modules need help
build_options = {
    'packages': [
        'google.generativeai',
        'whisperx',
        'yt_dlp',
        'pydub',
        'torch',
        'transformers',
        'numpy',
        'pandas',
        'scipy',
        'sklearn',
        'nltk',
        'pyannote.audio',
        'lightning',
        'http.server',
        'socketserver',
        'webbrowser',
        'json',
        'logging',
        'threading',
        'io',
        'datetime'
    ],
    'excludes': ['matplotlib', 'tkinter'],
    'include_files': [
        'config.py',
        'main.py', 
        'web_gui.py',
        'transcript_utils.py',
        'audio_utils.py',
        'quote_extraction.py',
        'utils.py',
        'requirements.txt'
    ]
}

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable(
        'run.py',
        base=base,
        target_name='YouTube-Quote-Extractor'
    )
]

setup(
    name='YouTube Quote Extractor',
    version='1.0',
    description='Extract transcripts and quotes from YouTube videos',
    options={'build_exe': build_options},
    executables=executables
)
```

### Step 3: Build
```bash
python setup.py build
```

## 🎯 Method 4: Nuitka (High Performance)

Nuitka compiles Python to C++ for better performance.

### Step 1: Install Nuitka
```bash
pip install nuitka
```

### Step 2: Compile
```bash
nuitka --standalone --onefile --enable-plugin=anti-bloat --windows-disable-console --output-filename=YouTube-Quote-Extractor run.py
```

## 📋 Pre-Build Checklist

Before creating your executable, ensure:

1. **Test your application thoroughly** in the current environment
2. **Create a clean virtual environment** and test installation from requirements.txt
3. **Check for any hardcoded paths** in your code
4. **Ensure all dependencies are properly listed** in requirements.txt
5. **Test on the target operating system** if different from development

## 🔧 Optimization Tips

### Reduce File Size
```bash
# Use UPX compression (install UPX first)
pyinstaller --onefile --upx-dir=/path/to/upx run.py

# Exclude unnecessary modules
pyinstaller --onefile --exclude-module matplotlib --exclude-module tkinter run.py
```

### Improve Startup Time
- Use directory distribution instead of single file
- Exclude unused packages
- Use lazy imports where possible

## 🚀 Distribution Package

Create a complete distribution package:

### Step 1: Create Distribution Folder
```
YouTube-Quote-Extractor-v1.0/
├── YouTube-Quote-Extractor.exe
├── README.txt
├── REQUIREMENTS.txt
├── LICENSE.txt
└── examples/
    └── sample_timestamps.txt
```

### Step 2: Create README.txt
```txt
YouTube Quote Extractor v1.0
=============================

QUICK START:
1. Double-click YouTube-Quote-Extractor.exe
2. Your web browser will open automatically
3. Enter a YouTube URL and timestamps
4. Click "Start Processing"

REQUIREMENTS:
- Internet connection for downloading videos
- Google Gemini API key (set as GEMINI_API_KEY environment variable)

SUPPORT:
For issues or questions, contact: [your-email]

FEATURES:
- Web-based interface (no technical knowledge required)
- AI-powered transcription using Google Gemini
- Intelligent quote extraction with context
- Live processing logs
- Advanced settings for customization
- Export results as text files

VERSION: 1.0
BUILT: [date]
```

## 🎨 Adding an Icon

1. Create or download an ICO file (Windows) or ICNS file (macOS)
2. Add to PyInstaller command:
```bash
pyinstaller --onefile --windowed --icon=icon.ico run.py
```

## 🧪 Testing Your Executable

1. **Test on a clean machine** without Python installed
2. **Test all features** including file downloads and API calls
3. **Check error handling** with invalid inputs
4. **Verify web browser opens correctly**
5. **Test with different operating systems** if targeting multiple platforms

## 📦 Platform-Specific Notes

### Windows
- Use `.exe` extension
- Consider code signing for trust
- Test with Windows Defender

### macOS
- Use `.app` bundle or DMG
- Handle Gatekeeper restrictions
- Consider notarization for distribution

### Linux
- Create `.AppImage` for universal compatibility
- Test on different distributions
- Include desktop entry file

## 🔒 Security Considerations

1. **Don't include API keys** in the executable
2. **Use environment variables** for sensitive data
3. **Consider code obfuscation** if needed
4. **Test with antivirus software** to avoid false positives

## 🎯 Recommended Build Command

For most users, this single command will work best:

```bash
pyinstaller --onefile --windowed --name "YouTube-Quote-Extractor" --add-data "config.py;." --add-data "*.py;." --hidden-import google.generativeai --hidden-import whisperx --hidden-import yt_dlp run.py
```

## 📞 Troubleshooting

### Common Issues:
1. **Missing modules**: Add to `--hidden-import`
2. **Large file size**: Use `--exclude-module` for unused packages
3. **Slow startup**: Use directory distribution instead of single file
4. **Path issues**: Use relative paths and `os.path.join()`
5. **API failures**: Ensure environment variables are accessible

### Debug Mode:
```bash
pyinstaller --onefile --console --debug all run.py
```

This will show detailed error messages during execution.

---

## 🎉 Final Steps

1. Build your executable using your preferred method
2. Test thoroughly on target machines
3. Create distribution package with documentation
4. Consider hosting on GitHub Releases for easy sharing
5. Provide clear installation and usage instructions

Your YouTube Quote Extractor is now ready for distribution! 🚀 