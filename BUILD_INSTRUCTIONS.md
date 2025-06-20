# Building YouTube Quote Extractor Executable

This guide explains how to create a standalone executable for the YouTube Quote Extractor that includes all dependencies, your `.env` configuration, and FFmpeg executables.

## Prerequisites

1. **Python Environment**: Ensure you have Python 3.8+ installed
2. **Virtual Environment**: Recommended to use a virtual environment
3. **Dependencies**: All requirements from `requirements.txt` installed

## Quick Build (Automated)

The easiest way to build the executable is using the automated build script:

```bash
python build_executable.py
```

This script will:
- ✅ Check all requirements
- ✅ Create `.env` template if missing
- ✅ Download FFmpeg if not present
- ✅ Install PyInstaller if needed
- ✅ Clean previous builds
- ✅ Build the executable with all dependencies

## Manual Build Process

If you prefer to build manually or need more control:

### Step 1: Prepare Environment File

Create a `.env` file in your project root with your configuration:

```env
# Required: Your Google Gemini API Key
GEMINI_API_KEY=your_google_gemini_api_key_here

# Optional: Custom settings
OUTPUT_DIR=./outputs
FFMPEG_LOCATION=./ffmpeg
AUDIO_QUALITY=192
MAX_FILE_SIZE_MB=100
MAX_DURATION_MINUTES=50
```

### Step 2: Download FFmpeg

The executable needs FFmpeg bundled. You can either:

**Option A: Use the download script (if available)**
```bash
python download_ffmpeg.py
```

**Option B: Manual download**
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract `ffmpeg.exe` and `ffprobe.exe` to a `ffmpeg/` folder in your project root

### Step 3: Install PyInstaller

```bash
pip install pyinstaller
```

### Step 4: Build the Executable

```bash
pyinstaller youtube_quote_extractor.spec --clean
```

## What Gets Bundled

The executable includes:

### Python Dependencies
- ✅ yt-dlp (YouTube downloading)
- ✅ google-generativeai (Gemini API)
- ✅ python-dotenv (Environment variables)
- ✅ tenacity (Retry logic)
- ✅ pydub (Audio processing)
- ✅ ratelimit (API rate limiting)
- ✅ grpcio (gRPC communication)
- ✅ pydantic (Data validation)
- ✅ streamlit (Web interface)
- ✅ All other required modules

### External Resources
- ✅ Your `.env` configuration file
- ✅ FFmpeg executable (`ffmpeg.exe`)
- ✅ FFprobe executable (`ffprobe.exe`)

### Runtime Setup
- ✅ Automatic PATH configuration for FFmpeg
- ✅ Environment variable loading from bundled `.env`
- ✅ Proper resource location detection

## Output

After successful build, you'll find:

```
dist/
└── YouTube Quote Extractor.exe    # Your standalone executable
```

## Distribution

The executable is completely self-contained and can be distributed as a single file. Recipients don't need:
- Python installed
- Any dependencies installed
- Separate FFmpeg installation
- Configuration files

## Troubleshooting

### Build Fails - Missing .env
**Error**: `.env file not found`
**Solution**: Create a `.env` file with your `GEMINI_API_KEY`

### Build Fails - Missing FFmpeg
**Error**: `FFmpeg executables not found`
**Solution**: Run `python download_ffmpeg.py` or manually download FFmpeg

### Runtime Error - API Key Missing
**Error**: `GEMINI_API_KEY not found in environment variables`
**Solution**: Ensure your `.env` file contains the correct API key before building

### Executable Too Large
The executable may be 100-200MB due to bundled dependencies. This is normal for a complete Python application with AI libraries.

### Antivirus False Positives
Some antivirus software may flag PyInstaller executables. This is a known issue with PyInstaller. You can:
1. Add an exception for the executable
2. Sign the executable with a code signing certificate
3. Distribute the source code instead

## Advanced Configuration

### Custom Icon
To add a custom icon, edit `youtube_quote_extractor.spec`:
```python
icon='path/to/your/icon.ico'
```

### Debug Mode
For debugging, change in the spec file:
```python
debug=True,
console=True,
```

### Smaller Executable
To reduce size, you can exclude unused modules in the spec file:
```python
excludes=[
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    # Add other unused modules
]
```

## File Structure

Your project should look like this before building:

```
youtube-quote-extractor/
├── run.py                          # Main entry point
├── web_gui.py                      # Web interface
├── main.py                         # Core functionality
├── config.py                       # Configuration
├── requirements.txt                # Python dependencies
├── .env                           # Your environment variables
├── ffmpeg/                        # FFmpeg executables
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── youtube_quote_extractor.spec   # PyInstaller spec
├── runtime_hook.py                # Runtime setup
└── build_executable.py           # Build script
```

## Support

If you encounter issues:
1. Check that all files are present
2. Verify your `.env` file has the correct API key
3. Ensure FFmpeg executables are in the `ffmpeg/` folder
4. Try the automated build script first
5. Check the build output for specific error messages 