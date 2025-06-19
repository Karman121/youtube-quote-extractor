# YouTube Quote Extractor

A sophisticated Python application that downloads YouTube videos, generates accurate transcripts using Google's Gemini AI, and extracts meaningful quotes for journalism and content creation.

## 🚀 Features

### Core Functionality
- **YouTube Audio Download**: High-quality audio extraction from YouTube videos
- **AI-Powered Transcription**: Uses Google Gemini 2.5 Flash for accurate speech-to-text
- **Smart Quote Extraction**: Contextual quote extraction with journalist-focused prompts
- **Chunked Processing**: Handles long videos (>50min or >100MB) with intelligent chunking
- **Caching System**: Avoids re-processing by caching audio and transcripts

### Interface Options
- **🎨 Modern GUI Application**: Beautiful, user-friendly interface with tabbed layout
- **💻 Command Line Interface**: Traditional CLI for power users and automation
- **🔄 Dual Mode Launcher**: Choose your preferred interface on startup

### Advanced Features
- **Context-Aware Processing**: Configurable before/after timestamp contexts
- **Speaker Identification**: Automatic speaker labeling in transcripts
- **Custom Prompts**: Fully customizable transcription and quote extraction prompts
- **Export Capabilities**: Save transcripts and quotes to text files
- **Progress Tracking**: Real-time status updates and progress indication

## 📋 Requirements

### System Requirements
- Python 3.8+
- FFmpeg (for audio processing)
- Google Gemini API key

### Python Dependencies
```
pip install -r requirements.txt
```

Key dependencies:
- `google-generativeai` - Google Gemini AI integration
- `yt-dlp` - YouTube video downloading
- `pydub` - Audio processing
- `ttkbootstrap` - Modern GUI framework
- `tenacity` - Retry logic for API calls

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd youtube-quote-extractor
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg**:
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

4. **Set up API key**:
   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```

## 🎯 Usage

### Quick Start
```bash
python run.py
```
This launches the interface selector where you can choose GUI or CLI mode.

### GUI Application (Recommended)
```bash
python gui_app.py
```

**Features:**
- **Processing Modes**: Choose between transcript-only or transcript + quotes
- **URL Validation**: Verify YouTube URLs before processing
- **Context Configuration**: Adjust before/after timestamp windows
- **Advanced Settings**: Customize AI prompts and instructions
- **Results Display**: Tabbed interface for transcripts and quotes
- **Export Functions**: Save results to files

### Command Line Interface
```bash
python main.py
```

**Usage Flow:**
1. Paste YouTube URL and timestamps
2. Configure context windows
3. Processing happens automatically
4. Results saved to `{video_title}_transcript.txt` and `{video_title}_quotes.txt`

## 📝 Input Format

### YouTube URL
Any valid YouTube URL format:
```
https://www.youtube.com/watch?v=VIDEO_ID
https://youtu.be/VIDEO_ID
```

### Timestamps (for quote extraction)
```
1:30 - Discussion about AI
2:45 - Important announcement  
5:20 - Q&A session begins
10:15
```

Supported formats:
- `MM:SS` - Minutes and seconds
- `HH:MM:SS` - Hours, minutes, and seconds
- Optional descriptions after `-` or ` - `

## ⚙️ Configuration

### Default Settings (`config.py`)
```python
DEFAULT_SETTINGS = {
    "chunk_length_minutes": 30,
    "overlap_seconds": 30,
    "max_file_size_mb": 100,
    "max_duration_minutes": 50,
    "default_context_after_seconds": 90,
    "default_context_before_seconds": 30,
    "gemini_model": "gemini-2.5-flash-preview-05-20",
    "retry_attempts": 3,
    "rate_limit_calls": 1.8,
    "rate_limit_period": 1,
    "audio_quality": "192",
    "output_directory": "."
}
```

### Custom Prompts
The application supports fully customizable prompts:

- **Transcription Prompt**: Controls how audio is transcribed
- **Quote Extraction Instructions**: 12 configurable rules for quote selection

Access these through the GUI's "Advanced Settings" tab or modify `config.py` directly.

## 📊 Code Quality Improvements

### Architecture Enhancements
- ✅ **Eliminated Code Duplication**: Centralized common functions
- ✅ **Modular Design**: Clean separation of concerns across modules
- ✅ **Configuration Management**: Centralized settings and prompts
- ✅ **Error Handling**: Comprehensive error management with retry logic
- ✅ **Async Processing**: Non-blocking GUI with threaded operations

### Function Breakdown
The main processing logic has been refactored into focused functions:
- `validate_input()` - Input validation
- `download_and_prepare_audio()` - Audio handling
- `get_or_create_transcript()` - Transcript management
- `process_timestamps()` - Quote extraction
- `save_quotes()` - File output

### Testing & Reliability
- **Retry Logic**: Automatic retry for API failures
- **Rate Limiting**: Respects API rate limits
- **Input Validation**: Comprehensive validation for URLs and timestamps
- **Graceful Degradation**: Handles errors without crashing

## 🎨 GUI Features

### Main Tab
- **Processing Mode Selection**: Transcript-only or full quote extraction
- **URL Input & Validation**: Real-time URL validation
- **Context Settings**: Configurable timestamp windows
- **Progress Tracking**: Visual progress indication
- **Control Buttons**: Start/Stop/Clear functionality

### Advanced Settings Tab
- **Custom Transcription Prompts**: Modify AI transcription behavior
- **Quote Extraction Rules**: Customize the 12 core instructions
- **Model Information**: View current AI model settings
- **Reset Functions**: Restore default settings

### Results Tab
- **Tabbed Results**: Separate views for transcripts and quotes
- **Export Functions**: Save results to custom file locations
- **Search & Navigation**: Easy browsing of generated content

## 🔧 Technical Details

### AI Integration
- **Model**: Google Gemini 2.5 Flash Preview
- **Context**: Uses video descriptions and user hints for better quote selection
- **Prompting**: Professional journalist-focused prompt engineering
- **Error Handling**: Automatic retry with exponential backoff

### Audio Processing
- **Format**: MP3 at 192kbps quality
- **Chunking**: Intelligent splitting for large files with overlap
- **Caching**: Avoids re-downloading existing audio files
- **Quality**: Optimized for speech recognition accuracy

### File Management
- **Naming**: Sanitized filenames based on video titles
- **Organization**: Logical file structure with clear naming conventions
- **Formats**: Plain text output for maximum compatibility
- **Encoding**: UTF-8 encoding for international character support

## 🐛 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**
- Ensure `.env` file exists with valid API key
- Check API key has appropriate permissions

**"FFmpeg not found"**
- Install FFmpeg system-wide
- Ensure FFmpeg is in system PATH

**"Failed to download audio"**
- Check internet connection
- Verify YouTube URL is accessible
- Some videos may have download restrictions

**GUI won't start**
- Install: `pip install ttkbootstrap`
- Try CLI mode as fallback

### Performance Tips
- Use transcript-only mode for faster processing
- Reduce context windows for quicker quote extraction
- Process shorter videos for faster results

## 📈 Future Enhancements

- [ ] Batch processing for multiple videos
- [ ] Support for other video platforms
- [ ] Integration with note-taking applications
- [ ] Advanced filtering and search capabilities
- [ ] Cloud deployment options
- [ ] API endpoint for external integrations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini AI for transcription and quote extraction
- yt-dlp project for YouTube download capabilities
- ttkbootstrap for the modern GUI framework
- The open-source community for various supporting libraries

---

**Made with ❤️ for journalists, content creators, and researchers** 