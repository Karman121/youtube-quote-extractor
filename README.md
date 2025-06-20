# 🎬 YouTube Quote Extractor

A professional AI-powered tool that downloads YouTube videos, generates accurate transcripts using Google's Gemini AI, extracts meaningful quotes, and provides intelligent analysis through natural language questions.

## 🚀 What This Tool Does

### Three Core Modes
The YouTube Quote Extractor is a sophisticated Python application that offers three powerful modes for video content analysis:

1.  **📝 Transcript Generation**: Downloads high-quality audio from any YouTube video and generates accurate, speaker-labeled transcripts using Google's Gemini AI.
2.  **💬 Quote Extraction**: Intelligently identifies and extracts meaningful quotes based on specific timestamps with configurable context windows.
3.  **🤔 AI Analysis & Questions**: Ask any question about the video content and get detailed, contextual answers powered by Gemini AI.

### Advanced AI Integration
-   **🤖 Multiple Gemini Models**: Choose from 8 different Gemini models to balance speed, cost, and quality.
-   **🔧 Fully Customizable Prompts**: Modify transcription instructions and quote extraction rules.
-   **📊 Context-Aware Processing**: Uses video descriptions and user context for better results.

### Key Features
-   **🌐 Modern Web Interface**: Beautiful, responsive web-based GUI that works on any device.
-   **⚡ Intelligent Chunking**: Handles long videos (50+ minutes) by splitting into manageable chunks with overlap.
-   **💾 Smart Caching**: Avoids re-processing by caching audio files and transcripts.
-   **🎯 Flexible Input**: Supports multiple timestamp formats with optional descriptions.
-   **📱 Cross-Platform**: Works on Windows, macOS, and Linux.
-   **🔄 Real-Time Updates**: Live processing logs and progress indication.

### Use Cases
-   **📰 Journalism**: Extract quotes from interviews, press conferences, and news segments.
-   **🎓 Research**: Analyze academic lectures, seminars, and educational content.
-   **📝 Content Creation**: Generate content from podcasts, webinars, and video discussions.
-   **📚 Documentation**: Create transcripts and summaries of important meetings or presentations.
-   **🔍 Content Analysis**: Ask specific questions about video content for insights and summaries.

## 📋 Requirements

### System Requirements
-   **Python**: 3.8 or higher
-   **FFmpeg**: For audio processing (installation instructions below)
-   **Internet Connection**: For YouTube downloads and AI processing
-   **Google Gemini API Key**: Free tier available at [Google AI Studio](https://makersuite.google.com/app/apikey)

### Python Dependencies
All dependencies are automatically installed via `requirements.txt`:
```
google-generativeai>=0.8.0
yt-dlp>=2024.1.0
python-dotenv>=1.0.0
tenacity>=8.2.0
pydub>=0.25.1
ratelimit>=2.2.1
```

## 🛠️ Installation

### Option 1: Download Pre-built Executables (Recommended)

**For Windows:**
-   Download: https://github.com/Karman121/youtube-quote-extractor/releases/download/v1.0.0/Youtube.Quote.Extractor.-.Windows.zip
-   Extract the zip file.
-   Place your `.env` file next to the executable (see Configuration section).
-   Double-click `YouTube Quote Extractor.exe` to run.

**For macOS:**
-   Download: https://github.com/Karman121/youtube-quote-extractor/releases/download/v1.0.0/Youtube.Quote.Extractor.-.Mac.zip
-   Extract the zip file.
-   Place your `.env` file next to the executable (see Configuration section).
-   Right-click the app and select "Open" (first time only due to security).

### Option 2: Install from Source

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd youtube-quote-extractor
    ```

2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install FFmpeg**:

    **Windows:**
    ```bash
    # Download FFmpeg automatically
    python get_ffmpeg.py
    ```

    **macOS:**
    ```bash
    brew install ffmpeg
    ```

    **Linux:**
    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```

4.  **Configure API Key**:
    Create a `.env` file in the project root:
    ```env
    GEMINI_API_KEY=your_google_gemini_api_key_here
    ```

## 🔑 Configuration

### API Key Setup
1.  Visit [Google AI Studio](https://makersuite.google.com/app/apikey).
2.  Create a free Google account if you don't have one.
3.  Generate a new API key.
4.  Create a `.env` file with your key:
    ```env
    GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ```

### Advanced Configuration (Optional)
The application includes comprehensive configuration options in `config.py`:

```python
DEFAULT_SETTINGS = {
    "chunk_length_minutes": 30,           # Max chunk size for long videos
    "overlap_seconds": 30,                # Overlap between chunks
    "max_file_size_mb": 100,             # Max file size before chunking
    "max_duration_minutes": 50,          # Max duration before chunking
    "default_context_after_seconds": 90,  # Context after timestamps
    "default_context_before_seconds": 30, # Context before timestamps
    "gemini_model": "gemini-1.5-flash",  # AI model to use
    "retry_attempts": 3,                 # API retry attempts
    "rate_limit_calls": 5,               # API calls per second
    "audio_quality": "192",              # Audio quality (kbps)
    "output_directory": "."              # Output file location
}
```

## 🎯 Usage

### Quick Start
```bash
python run.py
```
This launches the modern web interface in your browser automatically.

### Web Interface Features

**🏠 Main Tab:**
-   **Processing Mode Selection**: Choose between Transcript Only, Transcript + Quotes, and Transcript + Analysis.
-   **YouTube URL Input**: Paste any YouTube URL with automatic validation.
-   **Dynamic Input Sections**: Interface adapts based on selected mode.
-   **Real-time Processing**: Live progress updates and status messages.

**⚙️ Advanced Settings Tab:**
-   **AI Model Selection**: Choose from 8 different Gemini models.
-   **Custom Transcription Prompts**: Modify how the AI transcribes audio.
-   **Quote Extraction Rules**: Customize the 12 core extraction instructions.
-   **Save & Reset**: Preserve your settings or restore defaults.

**📊 Live Logs Tab:**
-   **Real-time Updates**: See processing steps as they happen.
-   **Color-coded Messages**: Success, warning, and error indicators.

## 🏗️ Building Executables with PyInstaller

### Prerequisites for Building
1.  Complete source installation (see Installation section).
2.  PyInstaller installed: `pip install pyinstaller`.
3.  `.env` file with your API key.
4.  FFmpeg installed (for Windows builds, use `python get_ffmpeg.py`).

### Build Process

**Step 1: Prepare Environment**
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
pip install pyinstaller

# Download FFmpeg (Windows only)
python get_ffmpeg.py
```

**Step 2: Build the Executable**
```bash
# Build using the spec file
pyinstaller youtube_quote_extractor.spec --clean
```

**Step 3: Locate Your Executable**
After successful build, find your application in the `dist/` directory.

### What Gets Bundled
The executable includes:
-   ✅ All Python dependencies and libraries
-   ✅ FFmpeg executables (for audio processing)
-   ✅ Runtime configuration and setup scripts
-   ❌ **`.env` file (external - must be provided by user)**

### Distribution Setup
When sharing your executable:

1.  **Share the executable file** (or a zip of the folder) from the `dist/` directory.
2.  **Provide setup instructions** for the `.env` file:
    ```
    Create a file named ".env" next to the executable with:
    GEMINI_API_KEY=your_api_key_here
    ```
3.  **Include this README** for complete usage instructions.

## 🚀 Advanced Usage

### Choosing the Right Model for Your Task

Selecting the right Gemini model is a trade-off between speed, cost, and analytical quality.

| Model Family      | Best For                                           | Key Trait                                       |
|-------------------|----------------------------------------------------|-------------------------------------------------|
| **Pro** | Deep analysis, complex questions, nuanced content  | Highest Quality & Reasoning                     |
| **Flash** | Quick transcripts, summaries, high-volume tasks    | Speed & Efficiency (Excellent Default)          |
| **Lite / Other** | Very fast, simple tasks where speed is critical    | Maximum Speed & Lowest Cost                     |

-   **For Maximum Quality (`gemini-1.5-pro`)**: This is the most capable model. Use it for the **Analysis Mode** when you need deep, accurate insights, or for transcribing videos with challenging audio or complex terminology. It is slower and costs more per API call.

-   **For Speed & Efficiency (`gemini-1.5-flash`)**: This model provides an excellent balance of performance and cost. **`gemini-1.5-flash` is the recommended default** for most tasks, including high-quality transcriptions and quote extractions, without the higher cost of the Pro model.

-   **For Experimental Features (`...-preview`)**: Use these models with caution. They offer access to the latest features but may be unstable or change without notice. Not recommended for critical production tasks.

### Analysis Mode Best Practices

**Effective Question Types:**
```
# Summarization Questions
"What are the 3 main points discussed in this video?"
"Summarize the key arguments presented by each speaker."

# Analysis Questions  
"What evidence does the speaker provide to support their claims?"
"How do the different speakers' perspectives compare on this topic?"

# Factual Questions
"What specific statistics or data points are mentioned?"
"What examples or case studies are referenced?"
```

## 📊 Output Example

### Transcript Output Format
```
=== TRANSCRIPT ===
Video: "How AI Will Change Everything"
URL: https://www.youtube.com/watch?v=...
Duration: 45:32
Generated: 2025-06-20 12:30:22

[00:00:15] Speaker 1: Welcome everyone to today's discussion about artificial intelligence...

[00:01:32] Speaker 2: That's a fascinating point. I think we need to consider...

[00:03:45] Speaker 1: Absolutely. The implications for the future are...
```

## 🐛 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found in environment variables"**
-   Ensure `.env` file exists in the same directory as the executable/script.
-   Verify the file contains: `GEMINI_API_KEY=your_actual_key`.
-   Check for typos in the key name (case-sensitive) and ensure no extra spaces.

**"FFmpeg not found"**
-   **Windows**: Run `python get_ffmpeg.py` before building.
-   **macOS**: Install via Homebrew: `brew install ffmpeg`.
-   **Linux**: Install via package manager: `sudo apt install ffmpeg`.

**"Failed to download audio from YouTube"**
-   Check your internet connection and verify the YouTube URL is valid and public.

**"API quota exceeded"**
-   You've hit the free tier limit for the Gemini API. Wait for the quota to reset or upgrade your account.

---

**🎬 Made with ❤️ for journalists, content creators, researchers, and anyone who needs to extract valuable insights from video content.**

*Transform hours of video into actionable quotes and transcripts in minutes with the power of AI.*
