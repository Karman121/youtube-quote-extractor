# 🎬 YouTube Quote Extractor

A professional AI-powered tool that downloads YouTube videos, generates accurate transcripts using Google's Gemini AI, extracts meaningful quotes, and provides intelligent analysis through natural language questions.

## 🚀 What This Tool Does

### Three Core Modes
The YouTube Quote Extractor is a sophisticated Python application that offers three powerful modes for video content analysis:

1. **📝 Transcript Generation**: Downloads high-quality audio from any YouTube video and generates accurate, speaker-labeled transcripts using Google's Gemini AI
2. **💬 Quote Extraction**: Intelligently identifies and extracts meaningful quotes based on specific timestamps with configurable context windows
3. **🤔 AI Analysis & Questions**: Ask any question about the video content and get detailed, contextual answers powered by Gemini AI

### Advanced AI Integration
- **🤖 Multiple Gemini Models**: Choose from 8 different Gemini models including:
  - `gemini-2.5-flash` (Default - Fast & Efficient)
  - `gemini-2.5-pro` (Most Capable)
  - `gemini-2.0-flash` (Latest Generation)
  - `gemini-1.5-flash`, `gemini-1.5-pro` (Proven Performance)
  - And 3 additional specialized models
- **🔧 Fully Customizable Prompts**: Modify transcription instructions and quote extraction rules
- **📊 Context-Aware Processing**: Uses video descriptions and user context for better results

### Key Features
- **🌐 Modern Web Interface**: Beautiful, responsive web-based GUI that works on any device
- **⚡ Intelligent Chunking**: Handles long videos (50+ minutes) by splitting into manageable chunks with overlap
- **💾 Smart Caching**: Avoids re-processing by caching audio files and transcripts
- **🎯 Flexible Input**: Supports multiple timestamp formats with optional descriptions
- **📱 Cross-Platform**: Works on Windows, macOS, and Linux
- **🔄 Real-Time Updates**: Live processing logs and progress indication

### Use Cases
- **📰 Journalism**: Extract quotes from interviews, press conferences, and news segments
- **🎓 Research**: Analyze academic lectures, seminars, and educational content
- **📝 Content Creation**: Generate content from podcasts, webinars, and video discussions
- **📚 Documentation**: Create transcripts and summaries of important meetings or presentations
- **🔍 Content Analysis**: Ask specific questions about video content for insights and summaries

## 📋 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **FFmpeg**: For audio processing (installation instructions below)
- **Internet Connection**: For YouTube downloads and AI processing
- **Google Gemini API Key**: Free tier available at [Google AI Studio](https://makersuite.google.com/app/apikey)

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
- Download: [YouTube Quote Extractor - Windows.zip](#) *(placeholder - add your link)*
- Extract the zip file
- Place your `.env` file next to the executable (see Configuration section)
- Double-click `YouTube Quote Extractor.exe` to run

**For macOS:**
- Download: [YouTube Quote Extractor - macOS.zip](#) *(placeholder - add your link)*
- Extract the zip file
- Place your `.env` file next to the executable (see Configuration section)
- Right-click the app and select "Open" (first time only due to security)

### Option 2: Install from Source

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd youtube-quote-extractor
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg**:
   
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

4. **Configure API Key**:
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```

## 🔑 Configuration

### API Key Setup
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a free Google account if you don't have one
3. Generate a new API key
4. Create a `.env` file with your key:
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
    "gemini_model": "gemini-2.5-flash",  # AI model to use
    "retry_attempts": 3,                 # API retry attempts
    "rate_limit_calls": 1.8,            # API calls per second
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
- **Processing Mode Selection**: Choose between three powerful modes:
  - **📝 Transcript Only**: Generate complete transcript with speaker identification
  - **💬 Transcript + Quotes**: Extract specific quotes from provided timestamps
  - **🤔 Transcript + Analysis**: Ask questions and get AI-powered insights
- **YouTube URL Input**: Paste any YouTube URL with automatic validation
- **Dynamic Input Sections**: Interface adapts based on selected mode
- **Real-time Processing**: Live progress updates and status messages

**⚙️ Advanced Settings Tab:**
- **AI Model Selection**: Choose from 8 different Gemini models:
  - `gemini-2.5-flash` (Default - Fast & Efficient)
  - `gemini-2.5-pro` (Most Capable)
  - `gemini-2.0-flash` (Latest Generation)
  - `gemini-2.0-flash-lite` (Lightweight)
  - `gemini-1.5-flash` (Proven Performance)
  - `gemini-1.5-flash-8b` (Optimized)
  - `gemini-1.5-pro` (Professional)
  - `gemini-2.5-flash-lite-preview-06-17` (Preview)
- **Custom Transcription Prompts**: Modify how the AI transcribes audio
- **Quote Extraction Rules**: Customize the 12 core extraction instructions
- **Save & Reset**: Preserve your settings or restore defaults

**📊 Live Logs Tab:**
- **Real-time Updates**: See processing steps as they happen
- **Color-coded Messages**: Success, warning, and error indicators
- **Detailed Progress**: Track download, transcription, and analysis phases

### Processing Modes Explained

**1. 📝 Transcript Only Mode:**
- Downloads audio from YouTube video
- Generates complete AI transcript with speaker labels
- Outputs: `{video_title}_transcript.txt`
- **Use Case**: Full video documentation, meeting minutes, lecture notes
- **Speed**: Fastest processing option

**2. 💬 Transcript + Quotes Mode:**
- Everything from Transcript Only mode
- Plus: Extracts specific quotes around provided timestamps
- **Context Settings**: Configurable before/after timestamp windows (30-90 seconds)
- **Timestamp Input**: Multiple formats supported with descriptions
- Outputs: `{video_title}_transcript.txt` + `{video_title}_quotes.txt`
- **Use Case**: Journalism, content creation, specific quote extraction

**3. 🤔 Transcript + Analysis Mode:**
- Everything from Transcript Only mode  
- Plus: AI-powered analysis based on your questions
- **Question Input**: Ask anything about the video content
- **Contextual Answers**: Uses full transcript and video description
- Outputs: `{video_title}_transcript.txt` + `{video_title}_analysis.txt`
- **Use Case**: Research analysis, content summarization, insight extraction

### Example Questions for Analysis Mode
```
What are the main points discussed in this video?

Summarize the key insights about AI development mentioned by the speakers.

What does the speaker think about the future of technology?

What are the most controversial statements made in this discussion?

Can you identify the different perspectives presented on this topic?

What evidence or examples does the speaker provide to support their arguments?
```

### Input Formats

**YouTube URLs:**
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://youtu.be/dQw4w9WgXcQ
https://youtube.com/watch?v=dQw4w9WgXcQ
```

**Timestamps for Quote Extraction:**
```
1:30 - Discussion about AI developments
2:45 - Important policy announcement
5:20 - Q&A session begins
10:15
15:30 - Closing remarks
```

**Supported Timestamp Formats:**
- `MM:SS` (e.g., `5:30`)
- `HH:MM:SS` (e.g., `1:05:30`)
- Optional descriptions after ` - `

## 🏗️ Building Executables with PyInstaller

### Prerequisites for Building
1. Complete source installation (see Installation section)
2. PyInstaller installed: `pip install pyinstaller`
3. `.env` file with your API key
4. FFmpeg installed (for Windows builds, use `python get_ffmpeg.py`)

### Build Process

**Step 1: Prepare Environment**
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
pip install pyinstaller

# Download FFmpeg (Windows only)
python get_ffmpeg.py

# Verify your .env file exists with API key
cat .env
```

**Step 2: Build the Executable**
```bash
# Clean any previous builds
rm -rf build dist

# Build using the spec file
pyinstaller youtube_quote_extractor.spec --clean
```

**Step 3: Locate Your Executable**
After successful build:
```
dist/
└── YouTube Quote Extractor.exe    # Windows
└── YouTube Quote Extractor        # macOS/Linux
```

### What Gets Bundled
The executable includes:
- ✅ All Python dependencies and libraries
- ✅ FFmpeg executables (for audio processing)
- ✅ Runtime configuration and setup scripts
- ❌ **`.env` file (external - must be provided by user)**

### Distribution Setup
When sharing your executable:

1. **Share the executable file** from the `dist/` folder
2. **Provide setup instructions** for the `.env` file:
   ```
   Create a file named ".env" next to the executable with:
   GEMINI_API_KEY=your_api_key_here
   ```
3. **Include this README** for complete usage instructions

### Build Troubleshooting

**Build fails with missing modules:**
```bash
pip install --upgrade -r requirements.txt
```

**FFmpeg not found during build:**
```bash
# Windows
python get_ffmpeg.py

# macOS/Linux
brew install ffmpeg  # or equivalent package manager
```

**Executable won't start:**
- Ensure `.env` file is in the same folder as the executable
- Check that your API key is valid
- Try running from command line to see error messages

**Large executable size (100-200MB):**
- This is normal due to bundled Python runtime and AI libraries
- The size ensures the executable works on any system without dependencies

## 🔧 Technical Architecture

### Core Modules

**`main.py`** - Core processing logic
- Video URL validation and processing
- Audio download and preparation
- Transcript generation coordination
- Quote extraction and context processing

**`web_gui.py`** - Modern web interface
- HTML/CSS/JavaScript frontend
- Python HTTP server backend
- Real-time progress updates
- Advanced settings management

**`transcript_utils.py`** - AI transcription handling
- Gemini AI integration
- Audio chunking for large files
- Speaker identification and labeling
- Caching system for efficiency

**`quote_extraction.py`** - Quote processing
- Timestamp parsing and validation
- Context window calculation
- AI-powered quote selection
- Output formatting and file generation

**`audio_utils.py`** - Audio processing
- YouTube audio download via yt-dlp
- Audio format conversion with pydub
- File size and duration management
- Quality optimization for speech recognition

**`config.py`** - Configuration management
- Default settings and parameters
- AI prompt templates
- Quote extraction instructions
- Error messages and success responses

**`utils.py`** - Shared utilities
- Filename sanitization
- Timestamp formatting
- Common helper functions

### AI Integration Details

**Models Available:** 8 Different Gemini Models
- **gemini-2.5-flash** (Default): Optimized for speed and efficiency, best balance of performance and cost
- **gemini-2.5-pro**: Most capable model with advanced reasoning and analysis capabilities
- **gemini-2.0-flash**: Latest generation with improved understanding and generation
- **gemini-2.0-flash-lite**: Lightweight version of the latest generation
- **gemini-1.5-flash**: Proven fast performance with reliable results
- **gemini-1.5-flash-8b**: Optimized 8-billion parameter model
- **gemini-1.5-pro**: Professional-grade model with enhanced capabilities
- **gemini-2.5-flash-lite-preview-06-17**: Preview version with experimental features

**Processing Capabilities:**
- **Transcription**: Long-form audio transcription with speaker identification
- **Quote Extraction**: Context-aware quote selection with journalist-focused rules
- **Content Analysis**: Natural language question answering with deep contextual understanding
- **Multi-modal Input**: Processes video descriptions alongside audio content

**Prompting Strategy:**
- **Transcription Prompts**: Professional audio transcriptionist instructions with speaker labeling
- **Quote Extraction**: 12 configurable rules optimized for journalism and content creation
- **Analysis Prompts**: Expert analyst framework for comprehensive content analysis
- **Context Integration**: Uses video metadata and user questions for targeted responses

**Error Handling:**
- Automatic retry with exponential backoff
- Rate limiting to respect API quotas
- Graceful degradation for API failures
- Comprehensive error logging with emoji-enhanced messages

### Performance Optimizations

**Chunking System:**
- Intelligent splitting of long videos
- Configurable overlap between chunks
- Maintains context across boundaries
- Parallel processing where possible

**Caching:**
- Audio files cached to avoid re-download
- Transcript caching for repeated processing
- Intelligent cache invalidation
- Configurable cache directory

**Memory Management:**
- Streaming audio processing
- Efficient file handling for large videos
- Garbage collection optimization
- Resource cleanup on completion

## 🐛 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found in environment variables"**
- Ensure `.env` file exists in the same directory as the executable/script
- Verify the file contains: `GEMINI_API_KEY=your_actual_key`
- Check for typos in the key name (case-sensitive)
- Ensure no extra spaces around the equals sign

**"FFmpeg not found"**
- **Windows**: Run `python get_ffmpeg.py` or install manually
- **macOS**: Install via Homebrew: `brew install ffmpeg`
- **Linux**: Install via package manager: `sudo apt install ffmpeg`
- Verify installation: `ffmpeg -version`

**"Failed to download audio from YouTube"**
- Check internet connection
- Verify the YouTube URL is accessible and public
- Some videos have download restrictions
- Try a different video to test

**"API quota exceeded"**
- You've hit the free tier limit for Gemini API
- Wait for quota reset (usually daily)
- Consider upgrading to paid tier for higher limits

**Web interface won't load**
- Check if port 8080 is available
- Try a different browser
- Disable browser extensions that might block local servers
- Check firewall settings

### Performance Tips

**For Faster Processing:**
- Use "Transcript Only" mode when you don't need quotes or analysis
- Choose `gemini-2.5-flash` or `gemini-2.0-flash-lite` for speed
- Process shorter videos (under 30 minutes) when possible
- Use higher-quality internet connection

**For Better Accuracy:**
- Choose `gemini-2.5-pro` or `gemini-1.5-pro` for complex content
- Ensure clear audio quality in source video
- Use videos with minimal background noise
- Provide descriptive timestamps for better quote context
- Use the advanced settings to customize prompts for your domain

**For Analysis Mode:**
- Ask specific, well-defined questions rather than broad queries
- Use `gemini-2.5-pro` for complex analytical tasks
- Break complex questions into smaller, focused ones
- Provide context in your questions when helpful
- Review video description first to inform your questions

**For Large Videos:**
- The system automatically chunks videos over 50 minutes
- Increase chunk overlap for better continuity
- Consider using analysis mode instead of extracting many quotes
- Ensure sufficient disk space for temporary files
- Use faster models for initial processing, then re-run with better models if needed

## 📊 Output Examples

### Transcript Output Format
```
=== TRANSCRIPT ===
Video: "How AI Will Change Everything"
URL: https://www.youtube.com/watch?v=example
Duration: 45:32
Generated: 2024-01-15 14:30:22

[00:00:15] Speaker 1: Welcome everyone to today's discussion about artificial intelligence...

[00:01:32] Speaker 2: That's a fascinating point. I think we need to consider...

[00:03:45] Speaker 1: Absolutely. The implications for the future are...
```

### Quote Output Format
```
=== EXTRACTED QUOTES ===
Video: "How AI Will Change Everything"
URL: https://www.youtube.com/watch?v=example
Context: 30 seconds before, 90 seconds after each timestamp

--- Quote 1 (Timestamp: 1:30) ---
Context: Discussion about AI developments

[00:01:00] Speaker 1: The current state of artificial intelligence is evolving rapidly...
[00:01:30] Speaker 2: "AI will fundamentally transform how we work, learn, and interact with technology in ways we're just beginning to understand."
[00:02:15] Speaker 1: This transformation will require careful consideration...

--- Quote 2 (Timestamp: 5:20) ---
Context: Q&A session begins

[00:04:50] Speaker 1: Now let's open the floor for questions...
[00:05:20] Audience Member: "What are the biggest challenges facing AI adoption in traditional industries?"
[00:06:30] Speaker 2: That's an excellent question. The main barriers include...
```

### Analysis Output Format
```
=== AI ANALYSIS ===
Video: "How AI Will Change Everything"
URL: https://www.youtube.com/watch?v=example
Question: "What are the main points discussed about AI's impact on employment?"
Generated: 2024-01-15 14:35:18

## Key Points on AI's Impact on Employment

### 1. Job Displacement Concerns
The speakers acknowledge that AI will automate certain roles, particularly in:
- Data entry and routine administrative tasks
- Basic customer service interactions
- Repetitive manufacturing processes

**Supporting Quote**: At [00:15:30], Speaker 2 states: "We can't ignore that some jobs will become obsolete, but history shows us that technology creates new opportunities even as it eliminates others."

### 2. New Job Categories Emerging
The discussion highlights several emerging roles:
- AI trainers and prompt engineers
- Human-AI collaboration specialists
- AI ethics and safety auditors

### 3. Reskilling and Adaptation
Both speakers emphasize the importance of:
- Continuous learning and adaptation
- Focus on uniquely human skills (creativity, empathy, complex problem-solving)
- Educational system reform to prepare for AI-integrated workplaces

**Key Insight**: The speakers agree that the transition period (next 5-10 years) will be critical for how society adapts to these changes.
```

## 🚀 Advanced Usage

### Choosing the Right Model for Your Task

**For Speed & Efficiency:**
- `gemini-2.5-flash` (Default) - Best for most use cases
- `gemini-2.0-flash-lite` - Fastest processing, good for simple transcripts
- `gemini-1.5-flash-8b` - Optimized performance for basic tasks

**For Maximum Quality:**
- `gemini-2.5-pro` - Best for complex analysis and detailed insights
- `gemini-1.5-pro` - Professional-grade results for important content
- `gemini-2.0-flash` - Latest technology with improved understanding

**For Experimental Features:**
- `gemini-2.5-flash-lite-preview-06-17` - Preview capabilities (may be unstable)

### Analysis Mode Best Practices

**Effective Question Types:**
```
# Summarization Questions
"What are the 3 main points discussed in this video?"
"Summarize the key arguments presented by each speaker."

# Analysis Questions  
"What evidence does the speaker provide to support their claims?"
"How do the different speakers' perspectives compare on this topic?"

# Insight Questions
"What are the implications of the ideas discussed for [specific industry/field]?"
"What questions remain unanswered after this discussion?"

# Factual Questions
"What specific statistics or data points are mentioned?"
"What examples or case studies are referenced?"
```

**Tips for Better Analysis Results:**
- Ask specific, focused questions rather than broad ones
- Reference particular aspects you're interested in
- Use follow-up questions to dive deeper into topics
- Consider the video's context and audience when framing questions

### Custom Prompt Engineering
Access advanced AI customization through the web interface:

1. Open the **Advanced Settings** tab
2. **Model Selection**: Choose the optimal Gemini model for your use case
3. **Transcription Prompts**: Modify for different transcription styles (formal, casual, technical)
4. **Quote Extraction Rules**: Customize the 12 core instructions for specific domains
5. **Save Settings**: Preserve your configurations for future use

### Integration with Other Tools
The output text files can be easily integrated with:
- **Note-taking apps**: Obsidian, Notion, Roam Research
- **Document processors**: Word, Google Docs, LaTeX
- **Content management systems**: WordPress, Ghost, Medium
- **Research tools**: Zotero, Mendeley, EndNote
- **Analysis platforms**: Excel, Google Sheets, Tableau

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository** on GitHub
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes** with clear commit messages
4. **Add tests** if applicable
5. **Submit a pull request** with a clear description

### Development Setup
```bash
# Clone your fork
git clone https://github.com/yourusername/youtube-quote-extractor.git
cd youtube-quote-extractor

# Install development dependencies
pip install -r requirements.txt
pip install black flake8 pytest  # Code formatting and testing

# Run tests
python -m pytest

# Format code
black .
```

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** - For providing advanced transcription and analysis capabilities
- **yt-dlp Project** - For robust YouTube download functionality
- **Python Community** - For the excellent ecosystem of libraries
- **Open Source Contributors** - For inspiration and code examples

## 📞 Support

- **Issues**: Report bugs and feature requests on GitHub Issues
- **Documentation**: This README covers most use cases
- **Community**: Join discussions in GitHub Discussions

---

**🎬 Made with ❤️ for journalists, content creators, researchers, and anyone who needs to extract valuable insights from video content.**

*Transform hours of video into actionable quotes and transcripts in minutes with the power of AI.* 