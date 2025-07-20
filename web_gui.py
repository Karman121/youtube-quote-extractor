#!/usr/bin/env python3
"""
Web GUI for YouTube Quote Extractor
A modern web interface for extracting quotes from YouTube videos
"""

import os
import sys
import json
import logging
import threading
import time
import webbrowser
import http.server
import socketserver
from datetime import datetime
from io import StringIO

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up log capture for web UI
log_capture_string = StringIO()

# Create a custom handler that writes to both console and our string buffer


class DualHandler(logging.Handler):
    def __init__(self, string_io):
        super().__init__()
        self.string_io = string_io
        
    def emit(self, record):
        msg = self.format(record)
        self.string_io.write(msg + '\n')
        print(msg)  # Also print to console


# Set up the dual logging handler BEFORE importing other modules
dual_handler = DualHandler(log_capture_string)
dual_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Configure root logger to use our dual handler
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()  # Clear existing handlers
root_logger.addHandler(dual_handler)

# Now import our modules - they will use the logging configuration set up
from config import (
    DEFAULT_SETTINGS, QUOTE_EXTRACTION_INSTRUCTIONS, TRANSCRIPTION_PROMPT
)
from main import (
    validate_url, validate_timestamps_format, parse_input,
    process_youtube_url_only, process_timestamps, process_analysis
)
from youtube_captions import (
    process_youtube_captions, process_timestamps_from_captions, 
    analyze_youtube_captions
)
from file_processor import (
    process_media_file, process_timestamps_from_file, analyze_file
)

logger = logging.getLogger(__name__)


class YouTubeExtractorHandler(http.server.SimpleHTTPRequestHandler):
    # Shared app state across all instances
    shared_app_state = {
        'processing': False,
        'status': 'Ready',
        'transcript': '',
        'quotes': [],
        'analysis': '',
        'video_title': '',
        'transcription_model': DEFAULT_SETTINGS['gemini_model'],
        'quote_extraction_model': DEFAULT_SETTINGS['gemini_model'],
        'analysis_model': DEFAULT_SETTINGS['gemini_model'],
        'transcription_prompt': TRANSCRIPTION_PROMPT,
        'quote_instructions': QUOTE_EXTRACTION_INSTRUCTIONS.copy(),
        'processing_type': 'youtube_audio',  # youtube_audio, youtube_captions, local_file
        'youtube_method': 'audio'  # audio or captions
    }
    
    def __init__(self, *args, **kwargs):
        # Use shared state instead of instance state
        self.app_state = self.shared_app_state
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_main_page()
        elif self.path == '/api/status':
            self.serve_status()
        elif self.path == '/api/results':
            self.serve_results()
        elif self.path == '/api/logs':
            self.serve_logs()
        elif self.path == '/api/settings':
            self.serve_settings()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/api/process':
            self.handle_process_request()
        elif self.path == '/api/process_file':
            self.handle_file_process_request()
        elif self.path == '/api/update_settings':
            self.handle_update_settings()
        elif self.path == '/api/clear':
            self.handle_clear_request()
        else:
            self.send_error(404)

    def serve_main_page(self):
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Quote Extractor</title>
    <!-- Markdown rendering library -->
    <script src="https://unpkg.com/marked@4.3.0/marked.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #ff6b9d 0%, #c44569 50%, #f8b500 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #ff6b9d 0%, #c44569 50%, #f8b500 100%);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 50%);
            pointer-events: none;
        }

        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            position: relative;
            z-index: 1;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }

        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }

        .tab {
            flex: 1;
            padding: 20px;
            background: none;
            border: none;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #6c757d;
            border-bottom: 3px solid transparent;
        }

        .tab:hover {
            background: #e9ecef;
            color: #495057;
        }

        .tab.active {
            background: white;
            color: #ff6b9d;
            border-bottom-color: #ff6b9d;
        }

        .tab-content {
            display: none;
            padding: 30px;
        }

        .tab-content.active {
            display: block;
        }

        .section {
            margin-bottom: 30px;
            padding: 25px;
            border: 2px solid #f1f3f4;
            border-radius: 15px;
            background: linear-gradient(135deg, #fafbfc 0%, #f8f9fa 100%);
            transition: all 0.3s ease;
        }
        
        .section:hover {
            border-color: #ff6b9d;
            box-shadow: 0 5px 15px rgba(255, 107, 157, 0.1);
        }
        
        .section h3 {
            color: #2d3436;
            margin-bottom: 15px;
            font-size: 1.3em;
            font-weight: 600;
        }

        input[type="text"], input[type="url"], input[type="number"], textarea, select {
            width: 100%;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 16px;
            font-family: inherit;
            background: white;
            transition: all 0.3s ease;
        }

        input[type="text"]:focus, input[type="url"]:focus, input[type="number"]:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #ff6b9d;
            box-shadow: 0 0 0 3px rgba(255, 107, 157, 0.1);
        }

        textarea {
            resize: vertical;
            min-height: 120px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            line-height: 1.5;
        }

        .radio-group {
            display: flex;
            gap: 25px;
            margin: 15px 0;
        }

        .radio-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 15px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        .radio-item:hover {
            background: rgba(255, 107, 157, 0.05);
        }
        
        input[type="radio"] {
            width: 20px;
            height: 20px;
            accent-color: #ff6b9d;
        }

        .context-settings {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }

        .context-item label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #495057;
        }
        
        .context-item input {
            width: 120px;
        }

        .hidden {
            display: none;
        }

        .buttons {
            display: flex;
            gap: 15px;
            margin-top: 30px;
            flex-wrap: wrap;
        }

        button {
            padding: 15px 30px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #ff6b9d 0%, #c44569 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(255, 107, 157, 0.4);
        }

        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(255, 107, 157, 0.6);
        }

        .btn-secondary {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            color: #495057;
            border: 2px solid #dee2e6;
        }

        .btn-secondary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-color: #ff6b9d;
        }

        .btn-danger {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
        }

        .btn-success {
            background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
            color: white;
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none !important;
            box-shadow: none !important;
        }

        .status {
            background: linear-gradient(135deg, #2d3436 0%, #636e72 100%);
            color: white;
            padding: 20px 30px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            font-weight: 500;
        }

        .results {
            margin-top: 30px;
            padding: 25px;
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-radius: 15px;
            border: 2px solid #e9ecef;
        }

        .result-tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #dee2e6;
        }

        .result-tab {
            padding: 12px 25px;
            background: none;
            border: none;
            border-bottom: 3px solid transparent;
            cursor: pointer;
            font-weight: 600;
            color: #6c757d;
            transition: all 0.3s ease;
        }

        .result-tab.active {
            border-bottom-color: #ff6b9d;
            color: #ff6b9d;
        }

        .result-content {
            background: white;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #dee2e6;
            min-height: 300px;
            white-space: pre-wrap;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            line-height: 1.6;
            overflow-y: auto;
            max-height: 500px;
        }

        /* Markdown styling for analysis content */
        .result-content h1, .result-content h2, .result-content h3, 
        .result-content h4, .result-content h5, .result-content h6 {
            color: #2d3436;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }

        .result-content h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 10px; }
        .result-content h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 8px; }
        .result-content h3 { font-size: 1.25em; }
        .result-content h4 { font-size: 1em; }
        .result-content h5 { font-size: 0.875em; }
        .result-content h6 { font-size: 0.85em; color: #6a737d; }

        .result-content p {
            margin-bottom: 16px;
            line-height: 1.6;
        }

        .result-content ul, .result-content ol {
            margin-bottom: 16px;
            padding-left: 30px;
        }

        .result-content li {
            margin-bottom: 8px;
            line-height: 1.5;
        }

        .result-content blockquote {
            margin: 16px 0;
            padding: 0 16px;
            color: #6a737d;
            border-left: 4px solid #dfe2e5;
            background: #f8f9fa;
            border-radius: 6px;
            padding: 16px;
        }

        .result-content code {
            background: #f6f8fa;
            border-radius: 3px;
            font-size: 85%;
            margin: 0;
            padding: 2px 4px;
            font-family: 'Monaco', 'Menlo', monospace;
        }

        .result-content pre {
            background: #f6f8fa;
            border-radius: 6px;
            font-size: 85%;
            line-height: 1.45;
            overflow: auto;
            padding: 16px;
            margin-bottom: 16px;
        }

        .result-content pre code {
            background: transparent;
            border: 0;
            display: inline;
            line-height: inherit;
            margin: 0;
            overflow: visible;
            padding: 0;
            word-wrap: normal;
        }

        .result-content strong {
            font-weight: 600;
            color: #24292e;
        }

        .result-content em {
            font-style: italic;
        }

        .result-content table {
            border-collapse: collapse;
            margin-bottom: 16px;
            width: 100%;
        }

        .result-content table th,
        .result-content table td {
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }

        .result-content table th {
            background: #f6f8fa;
            font-weight: 600;
        }

        .logs-container {
            background: #1a1a1a;
            color: #00ff00;
            padding: 20px;
            border-radius: 12px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 13px;
            line-height: 1.4;
            max-height: 400px;
            overflow-y: auto;
            border: 2px solid #333;
        }

        .log-entry {
            margin-bottom: 5px;
            padding: 2px 0;
        }

        .log-timestamp {
            color: #888;
        }

        .log-level-INFO {
            color: #00ff00;
        }

        .log-level-WARNING {
            color: #ffaa00;
        }

        .log-level-ERROR {
            color: #ff4444;
        }

        .advanced-section {
            margin-bottom: 25px;
        }

        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 15px;
            }
            
            .header {
                padding: 25px;
            }

            .header h1 {
                font-size: 2.2em;
            }
            
            .tabs {
                flex-direction: column;
            }

            .context-settings {
                grid-template-columns: 1fr;
            }

            .buttons {
                flex-direction: column;
            }

            button {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 YouTube Quote Extractor</h1>
            <p>Extract transcripts and quotes from YouTube videos with AI</p>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showMainTab('youtube')">🎥 YouTube</button>
            <button class="tab" onclick="showMainTab('files')">📁 Audio/Video Files</button>
            <button class="tab" onclick="showMainTab('advanced')">⚙️ Advanced</button>
            <button class="tab" onclick="showMainTab('logs')">📊 Live Logs</button>
        </div>

        <!-- YouTube Tab -->
        <div class="tab-content active" id="youtube-tab">
            <div class="section">
                <h3>1. YouTube URL</h3>
                <input type="url" id="url" placeholder="Enter YouTube URL here..." />
            </div>

            <div class="section">
                <h3>2. Transcription Method</h3>
                <div class="radio-group">
                    <div class="radio-item">
                        <input type="radio" id="youtube-captions" name="youtube-method" value="captions" checked />
                        <label for="youtube-captions">⚡ Auto-Captions (Fast & Free)</label>
                    </div>
                    <div class="radio-item">
                        <input type="radio" id="youtube-audio" name="youtube-method" value="audio" />
                        <label for="youtube-audio">🎵 Audio Transcription (High Quality)</label>
                    </div>
                </div>
                <p style="color: #666; font-size: 14px; margin-top: 10px;">
                    <strong>Auto-Captions:</strong> Uses YouTube's built-in captions - faster and free<br>
                    <strong>Audio Transcription:</strong> Downloads and transcribes audio with Gemini - slower but works with any video
                </p>
            </div>

            <div class="section">
                <h3>3. Processing Mode</h3>
                <div class="radio-group">
                    <div class="radio-item">
                        <input type="radio" id="transcript-only" name="mode" value="transcript" />
                        <label for="transcript-only">Generate Transcript Only</label>
                    </div>
                    <div class="radio-item">
                        <input type="radio" id="transcript-quotes" name="mode" value="both" checked />
                        <label for="transcript-quotes">Generate Transcript + Extract Quotes</label>
                    </div>
                    <div class="radio-item">
                        <input type="radio" id="transcript-analysis" name="mode" value="analysis" />
                        <label for="transcript-analysis">Generate Transcript + Ask Questions</label>
                    </div>
                </div>
            </div>

            <div class="section" id="quote-settings">
                <h3>4. Context Settings</h3>
                <div class="context-settings">
                    <div class="context-item">
                        <label for="context-before">Seconds Before:</label>
                        <input type="number" id="context-before" value="30" min="0" max="300" />
                    </div>
                    <div class="context-item">
                        <label for="context-after">Seconds After:</label>
                        <input type="number" id="context-after" value="60" min="0" max="600" />
                    </div>
                </div>
            </div>

            <div class="section" id="timestamps-section">
                <h3>5. Timestamps</h3>
                <p style="color: #666; margin-bottom: 10px;">Enter timestamps (MM:SS or HH:MM:SS) one per line:</p>
                <textarea id="timestamps" placeholder="1:30 - Discussion about AI&#10;2:45 - Important quote&#10;5:20 - Key insight"></textarea>
            </div>

            <div class="section hidden" id="question-section">
                <h3>4. Your Question</h3>
                <p style="color: #666; margin-bottom: 10px;">Ask any question about the video content:</p>
                <textarea id="user-question" placeholder="What are the main points discussed in this video?&#10;&#10;Summarize the key insights about AI development.&#10;&#10;What does the speaker think about the future of technology?"></textarea>
            </div>

            <div class="buttons">
                <button class="btn-primary" id="process-btn" onclick="startProcessing()">🚀 Start Processing</button>
                <button class="btn-danger" id="stop-btn" onclick="stopProcessing()" disabled>⏹ Stop</button>
                <button class="btn-secondary" onclick="clearAll()">🗑 Clear All</button>
            </div>

            <div class="results hidden" id="results">
                <div class="result-tabs">
                    <button class="result-tab active" onclick="showResultTab('transcript')">📝 Transcript</button>
                    <button class="result-tab" id="quotes-tab" onclick="showResultTab('quotes')">💬 Quotes</button>
                    <button class="result-tab" id="analysis-tab" onclick="showResultTab('analysis')">🤔 Analysis</button>
                </div>
                <div class="result-content" id="result-content"></div>
                <div style="margin-top: 15px;">
                    <button class="btn-secondary" onclick="downloadResult('transcript')">💾 Download Transcript</button>
                    <button class="btn-secondary" id="download-quotes-btn" onclick="downloadResult('quotes')">💾 Download Quotes</button>
                    <button class="btn-secondary" id="download-analysis-btn" onclick="downloadResult('analysis')">💾 Download Analysis</button>
                </div>
            </div>
        </div>

        <!-- Audio/Video Files Tab -->
        <div class="tab-content" id="files-tab">
            <div class="section">
                <h3>1. Select Audio/Video File</h3>
                <input type="file" id="file-input" accept="audio/*,video/*" style="padding: 20px; border: 2px dashed #ff6b9d; border-radius: 15px; background: #fafbfc;" />
                <p style="color: #666; font-size: 14px; margin-top: 10px;">
                    <strong>Supported formats:</strong><br>
                    📹 Video: MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V<br>
                    🎵 Audio: MP3, WAV, M4A, AAC, OGG, FLAC, WMA
                </p>
            </div>

            <div class="section">
                <h3>2. Processing Mode</h3>
                <div class="radio-group">
                    <div class="radio-item">
                        <input type="radio" id="file-transcript-only" name="file-mode" value="transcript" />
                        <label for="file-transcript-only">Generate Transcript Only</label>
                    </div>
                    <div class="radio-item">
                        <input type="radio" id="file-transcript-quotes" name="file-mode" value="both" checked />
                        <label for="file-transcript-quotes">Generate Transcript + Extract Quotes</label>
                    </div>
                    <div class="radio-item">
                        <input type="radio" id="file-transcript-analysis" name="file-mode" value="analysis" />
                        <label for="file-transcript-analysis">Generate Transcript + Ask Questions</label>
                    </div>
                </div>
            </div>

            <div class="section" id="file-quote-settings">
                <h3>3. Context Settings</h3>
                <div class="context-settings">
                    <div class="context-item">
                        <label for="file-context-before">Seconds Before:</label>
                        <input type="number" id="file-context-before" value="30" min="0" max="300" />
                    </div>
                    <div class="context-item">
                        <label for="file-context-after">Seconds After:</label>
                        <input type="number" id="file-context-after" value="60" min="0" max="600" />
                    </div>
                </div>
            </div>

            <div class="section" id="file-timestamps-section">
                <h3>4. Timestamps</h3>
                <p style="color: #666; margin-bottom: 10px;">Enter timestamps (MM:SS or HH:MM:SS) one per line:</p>
                <textarea id="file-timestamps" placeholder="1:30 - Discussion about AI&#10;2:45 - Important quote&#10;5:20 - Key insight"></textarea>
            </div>

            <div class="section hidden" id="file-question-section">
                <h3>3. Your Question</h3>
                <p style="color: #666; margin-bottom: 10px;">Ask any question about the file content:</p>
                <textarea id="file-user-question" placeholder="What are the main points discussed in this audio?&#10;&#10;Summarize the key insights.&#10;&#10;What topics are covered in this recording?"></textarea>
            </div>

            <div class="buttons">
                <button class="btn-primary" id="file-process-btn" onclick="startFileProcessing()">🚀 Start Processing</button>
                <button class="btn-danger" id="file-stop-btn" onclick="stopProcessing()" disabled>⏹ Stop</button>
                <button class="btn-secondary" onclick="clearAllFiles()">🗑 Clear All</button>
            </div>

            <div class="results hidden" id="file-results">
                <div class="result-tabs">
                    <button class="result-tab active" onclick="showFileResultTab('transcript')">📝 Transcript</button>
                    <button class="result-tab" id="file-quotes-tab" onclick="showFileResultTab('quotes')">💬 Quotes</button>
                    <button class="result-tab" id="file-analysis-tab" onclick="showFileResultTab('analysis')">🤔 Analysis</button>
                </div>
                <div class="result-content" id="file-result-content"></div>
                <div style="margin-top: 15px;">
                    <button class="btn-secondary" onclick="downloadResult('transcript')">💾 Download Transcript</button>
                    <button class="btn-secondary" id="file-download-quotes-btn" onclick="downloadResult('quotes')">💾 Download Quotes</button>
                    <button class="btn-secondary" id="file-download-analysis-btn" onclick="downloadResult('analysis')">💾 Download Analysis</button>
                </div>
            </div>
        </div>

        <!-- Advanced Tab -->
        <div class="tab-content" id="advanced-tab">
            <div class="advanced-section">
                <h3>🤖 AI Model Settings</h3>
                <div class="section">
                    <label for="transcription-model">Transcription Model:</label>
                    <select id="transcription-model">
                        <option value="gemini-2.5-flash" selected>gemini-2.5-flash (Default)</option>
                        <option value="gemini-2.5-pro">gemini-2.5-pro</option>
                        <option value="gemini-2.5-flash-lite-preview-06-17">gemini-2.5-flash-lite-preview-06-17</option>
                        <option value="gemini-2.0-flash">gemini-2.0-flash</option>
                        <option value="gemini-2.0-flash-lite">gemini-2.0-flash-lite</option>
                        <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                        <option value="gemini-1.5-flash-8b">gemini-1.5-flash-8b</option>
                        <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                    </select>
                    <p style="color: #666; font-size: 12px; margin-top: 5px;">Used for audio transcription tasks</p>
                </div>
                
                <div class="section">
                    <label for="quote-extraction-model">Quote Extraction Model:</label>
                    <select id="quote-extraction-model">
                        <option value="gemini-2.5-flash" selected>gemini-2.5-flash (Default)</option>
                        <option value="gemini-2.5-pro">gemini-2.5-pro</option>
                        <option value="gemini-2.5-flash-lite-preview-06-17">gemini-2.5-flash-lite-preview-06-17</option>
                        <option value="gemini-2.0-flash">gemini-2.0-flash</option>
                        <option value="gemini-2.0-flash-lite">gemini-2.0-flash-lite</option>
                        <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                        <option value="gemini-1.5-flash-8b">gemini-1.5-flash-8b</option>
                        <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                    </select>
                    <p style="color: #666; font-size: 12px; margin-top: 5px;">Used for extracting quotes from transcripts</p>
                </div>
                
                <div class="section">
                    <label for="analysis-model">Analysis Model:</label>
                    <select id="analysis-model">
                        <option value="gemini-2.5-flash" selected>gemini-2.5-flash (Default)</option>
                        <option value="gemini-2.5-pro">gemini-2.5-pro</option>
                        <option value="gemini-2.5-flash-lite-preview-06-17">gemini-2.5-flash-lite-preview-06-17</option>
                        <option value="gemini-2.0-flash">gemini-2.0-flash</option>
                        <option value="gemini-2.0-flash-lite">gemini-2.0-flash-lite</option>
                        <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                        <option value="gemini-1.5-flash-8b">gemini-1.5-flash-8b</option>
                        <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                    </select>
                    <p style="color: #666; font-size: 12px; margin-top: 5px;">Used for content analysis and question answering</p>
                </div>
            </div>

            <div class="advanced-section">
                <h3>📝 Transcription Prompt</h3>
                <div class="section">
                    <textarea id="transcription-prompt" rows="6" placeholder="Enter transcription prompt..."></textarea>
                </div>
            </div>

            <div class="advanced-section">
                <h3>💬 Quote Extraction Instructions</h3>
                <div class="section">
                    <textarea id="quote-instructions" rows="12" placeholder="Enter quote extraction instructions (one per line)..."></textarea>
                </div>
            </div>

            <div class="buttons">
                <button class="btn-success" onclick="saveAdvancedSettings()">💾 Save Settings</button>
                <button class="btn-secondary" onclick="resetAdvancedSettings()">🔄 Reset to Defaults</button>
            </div>
        </div>

        <!-- Logs Tab -->
        <div class="tab-content" id="logs-tab">
            <div class="section">
                <h3>📊 Live Processing Logs</h3>
                <div class="logs-container" id="logs-container">
                    <div class="log-entry">Ready to process...</div>
                </div>
                <div style="margin-top: 15px;">
                    <button class="btn-secondary" onclick="refreshLogs()">🔄 Refresh</button>
                </div>
            </div>
        </div>
        
        <div class="status" id="status">Ready</div>
    </div>

    <script>
        let currentResults = { transcript: '', quotes: [], analysis: '', video_title: '' };
        let currentTab = 'transcript';
        let currentMainTab = 'youtube';
        let logUpdateInterval;
        
        // Initialize advanced settings after a short delay
        setTimeout(function() {
            loadAdvancedSettings();
            
            // Debug: Check if marked library loaded
            console.log('🔍 Checking markdown library...');
            if (typeof marked !== 'undefined') {
                console.log('✅ Marked library loaded successfully');
                console.log('📋 Marked type:', typeof marked);
                console.log('📋 Marked.parse:', typeof marked.parse);
                
                // Test markdown rendering
                const testMarkdown = '# Test\\n**Bold text** and *italic text*';
                try {
                    let result;
                    if (typeof marked.parse === 'function') {
                        result = marked.parse(testMarkdown);
                    } else if (typeof marked === 'function') {
                        result = marked(testMarkdown);
                    }
                    console.log('✅ Test render successful:', result);
                } catch (e) {
                    console.error('❌ Test render failed:', e);
                }
            } else {
                console.error('❌ Marked library not loaded');
            }
        }, 500);
        
        // Toggle settings based on mode for YouTube tab
        document.querySelectorAll('input[name="mode"]').forEach(radio => {
            radio.addEventListener('change', function() {
                const quoteSettings = document.getElementById('quote-settings');
                const timestampsSection = document.getElementById('timestamps-section');
                const questionSection = document.getElementById('question-section');
                
                if (this.value === 'transcript') {
                    // Transcript only - hide all extra sections
                    quoteSettings.classList.add('hidden');
                    timestampsSection.classList.add('hidden');
                    questionSection.classList.add('hidden');
                } else if (this.value === 'both') {
                    // Extract quotes - show quote settings and timestamps
                    quoteSettings.classList.remove('hidden');
                    timestampsSection.classList.remove('hidden');
                    questionSection.classList.add('hidden');
                } else if (this.value === 'analysis') {
                    // Ask questions - show only question section
                    quoteSettings.classList.add('hidden');
                    timestampsSection.classList.add('hidden');
                    questionSection.classList.remove('hidden');
                }
            });
        });

        // Toggle settings based on mode for Files tab
        document.querySelectorAll('input[name="file-mode"]').forEach(radio => {
            radio.addEventListener('change', function() {
                const fileQuoteSettings = document.getElementById('file-quote-settings');
                const fileTimestampsSection = document.getElementById('file-timestamps-section');
                const fileQuestionSection = document.getElementById('file-question-section');
                
                if (this.value === 'transcript') {
                    // Transcript only - hide all extra sections
                    fileQuoteSettings.classList.add('hidden');
                    fileTimestampsSection.classList.add('hidden');
                    fileQuestionSection.classList.add('hidden');
                } else if (this.value === 'both') {
                    // Extract quotes - show quote settings and timestamps
                    fileQuoteSettings.classList.remove('hidden');
                    fileTimestampsSection.classList.remove('hidden');
                    fileQuestionSection.classList.add('hidden');
                } else if (this.value === 'analysis') {
                    // Ask questions - show only question section
                    fileQuoteSettings.classList.add('hidden');
                    fileTimestampsSection.classList.add('hidden');
                    fileQuestionSection.classList.remove('hidden');
                }
            });
        });
        
        function showMainTab(tab) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tabBtn => {
                tabBtn.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tab + '-tab').classList.add('active');
            
            // Add active class to clicked tab
            document.querySelector('[onclick="showMainTab(\\'' + tab + '\\')"]').classList.add('active');
            
            currentMainTab = tab;
            
            // Start log updates if logs tab is active
            if (tab === 'logs') {
                startLogUpdates();
            } else {
                stopLogUpdates();
            }
        }
        
        function startLogUpdates() {
            refreshLogs();
            logUpdateInterval = setInterval(refreshLogs, 1000); // Update every second during processing
        }
        
        function stopLogUpdates() {
            if (logUpdateInterval) {
                clearInterval(logUpdateInterval);
                logUpdateInterval = null;
            }
        }
        
        function refreshLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('logs-container');
                    container.innerHTML = '';
                    
                    if (data.logs && data.logs.length > 0) {
                        data.logs.forEach(log => {
                            const logEntry = document.createElement('div');
                            logEntry.className = 'log-entry';
                            logEntry.innerHTML = '<span class="log-timestamp">' + log.timestamp + '</span> <span class="log-level-' + log.level + '">[' + log.level + ']</span> ' + log.message;
                            container.appendChild(logEntry);
                        });
                        container.scrollTop = container.scrollHeight;
                    } else {
                        container.innerHTML = '<div class="log-entry">No logs available...</div>';
                    }
                })
                .catch(error => {
                    console.error('Error fetching logs:', error);
                });
        }
        
        function loadAdvancedSettings() {
            fetch('/api/settings')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('transcription-model').value = data.transcription_model;
                    document.getElementById('quote-extraction-model').value = data.quote_extraction_model;
                    document.getElementById('analysis-model').value = data.analysis_model;
                    document.getElementById('transcription-prompt').value = data.transcription_prompt;
                    
                    // Load quote instructions as text
                    document.getElementById('quote-instructions').value = data.quote_instructions.join('\\n');
                })
                .catch(error => {
                    console.error('Error loading settings:', error);
                });
        }
        
        function saveAdvancedSettings() {
            const transcriptionModel = document.getElementById('transcription-model').value;
            const quoteExtractionModel = document.getElementById('quote-extraction-model').value;
            const analysisModel = document.getElementById('analysis-model').value;
            const transcriptionPrompt = document.getElementById('transcription-prompt').value;
            const quoteInstructionsText = document.getElementById('quote-instructions').value;
            
            // Split by lines and filter out empty lines
            const instructions = quoteInstructionsText.split('\\n')
                .map(line => line.trim())
                .filter(line => line.length > 0);
            
            const settings = {
                transcription_model: transcriptionModel,
                quote_extraction_model: quoteExtractionModel,
                analysis_model: analysisModel,
                transcription_prompt: transcriptionPrompt,
                quote_instructions: instructions
            };
            
            fetch('/api/update_settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            }).then(response => response.json())
              .then(result => {
                  if (result.success) {
                      alert('✅ Settings saved successfully!');
                  } else {
                      alert('❌ Error saving settings: ' + result.error);
                  }
              }).catch(error => {
                  alert('❌ Error: ' + error);
              });
        }
        
        function resetAdvancedSettings() {
            if (confirm('Are you sure you want to reset all settings to defaults?')) {
                loadAdvancedSettings();
                alert('✅ Settings reset to defaults!');
            }
        }
        
        function startProcessing() {
            const url = document.getElementById('url').value.trim();
            const mode = document.querySelector('input[name="mode"]:checked').value;
            const timestamps = document.getElementById('timestamps').value.trim();
            const userQuestion = document.getElementById('user-question').value.trim();
            const contextBefore = document.getElementById('context-before').value;
            const contextAfter = document.getElementById('context-after').value;
            
            if (!url) {
                alert('Please enter a YouTube URL!');
                return;
            }
            
            if (mode === 'both' && !timestamps) {
                alert('Please enter timestamps for quote extraction!');
                return;
            }
            
            if (mode === 'analysis' && !userQuestion) {
                alert('Please enter a question for analysis!');
                return;
            }
            
            document.getElementById('process-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
            document.getElementById('status').textContent = 'Starting processing...';
            
            // Switch to logs tab automatically to show progress
            showMainTab('logs');
            
            const youtubeMethod = document.querySelector('input[name="youtube-method"]:checked').value;
            const processingType = youtubeMethod === 'captions' ? 'youtube_captions' : 'youtube_audio';
            
            const data = {
                url: url,
                mode: mode,
                timestamps: timestamps,
                user_question: userQuestion,
                context_before: parseInt(contextBefore),
                context_after: parseInt(contextAfter),
                youtube_method: youtubeMethod,
                processing_type: processingType
            };
            
            fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(response => response.json())
              .then(result => {
                  if (result.success) {
                      // Start polling for completion
                      startProcessingPolling();
                  } else {
                      alert('Error: ' + result.error);
                      document.getElementById('status').textContent = 'Error: ' + result.error;
                      processingComplete();
                  }
              }).catch(error => {
                  alert('Error: ' + error);
                  document.getElementById('status').textContent = 'Error: ' + error;
                  processingComplete();
              });
        }
        
        function startFileProcessing() {
            const fileInput = document.getElementById('file-input');
            const mode = document.querySelector('input[name="file-mode"]:checked').value;
            const timestamps = document.getElementById('file-timestamps').value.trim();
            const userQuestion = document.getElementById('file-user-question').value.trim();
            const contextBefore = document.getElementById('file-context-before').value;
            const contextAfter = document.getElementById('file-context-after').value;
            
            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Please select an audio or video file!');
                return;
            }
            
            if (mode === 'both' && !timestamps) {
                alert('Please enter timestamps for quote extraction!');
                return;
            }
            
            if (mode === 'analysis' && !userQuestion) {
                alert('Please enter a question for analysis!');
                return;
            }
            
            document.getElementById('file-process-btn').disabled = true;
            document.getElementById('file-stop-btn').disabled = false;
            document.getElementById('status').textContent = 'Uploading and processing file...';
            
            // Switch to logs tab automatically to show progress
            showMainTab('logs');
            
            // Create FormData for file upload
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('mode', mode);
            formData.append('timestamps', timestamps);
            formData.append('user_question', userQuestion);
            formData.append('context_before', contextBefore);
            formData.append('context_after', contextAfter);
            formData.append('processing_type', 'local_file');
            
            fetch('/api/process_file', {
                method: 'POST',
                body: formData
            }).then(response => response.json())
              .then(result => {
                  if (result.success) {
                      // Start polling for completion
                      startProcessingPolling();
                  } else {
                      alert('Error: ' + result.error);
                      document.getElementById('status').textContent = 'Error: ' + result.error;
                      fileProcessingComplete();
                  }
              }).catch(error => {
                  alert('Error: ' + error);
                  document.getElementById('status').textContent = 'Error: ' + error;
                  fileProcessingComplete();
              });
        }
        
        function fileProcessingComplete() {
            document.getElementById('file-process-btn').disabled = false;
            document.getElementById('file-stop-btn').disabled = true;
            stopProcessingPolling();
            // Clear any processing intervals
            stopLogUpdates();
        }
        
        function clearAllFiles() {
            stopProcessingPolling();
            stopLogUpdates();
            document.getElementById('file-input').value = '';
            document.getElementById('file-timestamps').value = '';
            document.getElementById('file-user-question').value = '';
            document.getElementById('file-results').classList.add('hidden');
            currentResults = { transcript: '', quotes: [], analysis: '', video_title: '' };
            document.getElementById('status').textContent = 'Cleared all file fields';
            // Reset processing buttons
            document.getElementById('file-process-btn').disabled = false;
            document.getElementById('file-stop-btn').disabled = true;
        }
        
        let processingPollingInterval;
        
        function startProcessingPolling() {
            processingPollingInterval = setInterval(checkProcessingStatus, 2000); // Check every 2 seconds
        }
        
        function stopProcessingPolling() {
            if (processingPollingInterval) {
                clearInterval(processingPollingInterval);
                processingPollingInterval = null;
            }
        }
        
        function checkProcessingStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status;
                    
                    if (!data.processing) {
                        // Processing is complete, get results
                        stopProcessingPolling();
                        fetch('/api/results')
                            .then(response => response.json())
                            .then(resultData => {
                                currentResults = resultData;
                                if (currentResults.transcript) {
                                    // Show results in the correct tab based on processing type
                                    fetch('/api/settings')
                                        .then(response => response.json())
                                        .then(settingsData => {
                                            const processingType = settingsData.processing_type || 'youtube_audio';
                                            
                                            if (processingType === 'local_file') {
                                                showFileResults();
                                                document.getElementById('status').textContent = 'File processing completed successfully!';
                                                // Switch back to Files tab to show results
                                                if (currentMainTab === 'logs') {
                                                    showMainTab('files');
                                                }
                                                fileProcessingComplete();
                                            } else {
                                                showResults();
                                                document.getElementById('status').textContent = 'Processing completed successfully!';
                                                // Switch back to YouTube tab to show results
                                                if (currentMainTab === 'logs') {
                                                    showMainTab('youtube');
                                                }
                                                processingComplete();
                                            }
                                        })
                                        .catch(error => {
                                            console.error('Error fetching processing type:', error);
                                            // Default to YouTube results
                                            showResults();
                                            document.getElementById('status').textContent = 'Processing completed successfully!';
                                            if (currentMainTab === 'logs') {
                                                showMainTab('youtube');
                                            }
                                            processingComplete();
                                        });
                                } else {
                                    document.getElementById('status').textContent = 'Processing failed - no results';
                                    processingComplete();
                                    fileProcessingComplete();
                                }
                            })
                            .catch(error => {
                                console.error('Error fetching results:', error);
                                document.getElementById('status').textContent = 'Error fetching results';
                                processingComplete();
                                fileProcessingComplete();
                            });
                    }
                })
                .catch(error => {
                    console.error('Error checking status:', error);
                    stopProcessingPolling();
                    processingComplete();
                    fileProcessingComplete();
                });
        }
        
        function stopProcessing() {
            stopProcessingPolling();
            stopLogUpdates();
            fetch('/api/clear', { method: 'POST' });
            processingComplete();
            fileProcessingComplete();
            document.getElementById('status').textContent = 'Processing stopped';
        }
        
        function processingComplete() {
            document.getElementById('process-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;
            stopProcessingPolling();
        }
        
        function clearAll() {
            stopProcessingPolling();
            document.getElementById('url').value = '';
            document.getElementById('timestamps').value = '';
            document.getElementById('user-question').value = '';
            document.getElementById('results').classList.add('hidden');
            currentResults = { transcript: '', quotes: [], analysis: '', video_title: '' };
            document.getElementById('status').textContent = 'Cleared all fields';
        }
        
        function showResults() {
            document.getElementById('results').classList.remove('hidden');
            document.getElementById('quotes-tab').style.display = currentResults.quotes.length > 0 ? 'block' : 'none';
            document.getElementById('analysis-tab').style.display = currentResults.analysis ? 'block' : 'none';
            document.getElementById('download-quotes-btn').style.display = currentResults.quotes.length > 0 ? 'inline-block' : 'none';
            document.getElementById('download-analysis-btn').style.display = currentResults.analysis ? 'inline-block' : 'none';
            showResultTab('transcript');
        }
        
        function showFileResults() {
            document.getElementById('file-results').classList.remove('hidden');
            document.getElementById('file-quotes-tab').style.display = currentResults.quotes.length > 0 ? 'block' : 'none';
            document.getElementById('file-analysis-tab').style.display = currentResults.analysis ? 'block' : 'none';
            document.getElementById('file-download-quotes-btn').style.display = currentResults.quotes.length > 0 ? 'inline-block' : 'none';
            document.getElementById('file-download-analysis-btn').style.display = currentResults.analysis ? 'inline-block' : 'none';
            showFileResultTab('transcript');
        }
        
        function showResultTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.result-tab').forEach(t => t.classList.remove('active'));
            document.querySelector('[onclick="showResultTab(\\'' + tab + '\\')"]').classList.add('active');
            
            const content = document.getElementById('result-content');
            if (tab === 'transcript') {
                content.innerHTML = '';
                content.textContent = currentResults.transcript || 'No transcript available';
            } else if (tab === 'quotes') {
                content.innerHTML = '';
                content.textContent = currentResults.quotes.join('\\n\\n') || 'No quotes available';
            } else if (tab === 'analysis') {
                const analysisText = currentResults.analysis || 'No analysis available';
                try {
                    if (typeof marked !== 'undefined') {
                        // Try different API calls for different versions of marked
                        let htmlContent;
                        if (typeof marked.parse === 'function') {
                            htmlContent = marked.parse(analysisText);
                        } else if (typeof marked === 'function') {
                            htmlContent = marked(analysisText);
                        } else {
                            throw new Error('marked API not recognized');
                        }
                        
                        // Render as markdown with better styling
                        content.innerHTML = htmlContent;
                        content.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segue UI", Roboto, sans-serif';
                        content.style.lineHeight = '1.6';
                        content.style.whiteSpace = 'normal';
                        console.log('✅ Markdown rendered successfully');
                    } else {
                        throw new Error('marked library not loaded');
                    }
                } catch (error) {
                    console.warn('⚠️ Markdown rendering failed:', error);
                    // Fallback to plain text if marked is not available
                    content.innerHTML = '';
                    content.textContent = analysisText;
                }
            }
        }
        
        function showFileResultTab(tab) {
            currentTab = tab;
            // Update file result tabs
            const fileResultTabs = document.querySelectorAll('#file-results .result-tab');
            fileResultTabs.forEach(t => t.classList.remove('active'));
            document.querySelector('#file-results [onclick="showFileResultTab(\\'' + tab + '\\')"]').classList.add('active');
            
            const content = document.getElementById('file-result-content');
            if (tab === 'transcript') {
                content.innerHTML = '';
                content.textContent = currentResults.transcript || 'No transcript available';
            } else if (tab === 'quotes') {
                content.innerHTML = '';
                content.textContent = currentResults.quotes.join('\\n\\n') || 'No quotes available';
            } else if (tab === 'analysis') {
                const analysisText = currentResults.analysis || 'No analysis available';
                try {
                    if (typeof marked !== 'undefined') {
                        // Try different API calls for different versions of marked
                        let htmlContent;
                        if (typeof marked.parse === 'function') {
                            htmlContent = marked.parse(analysisText);
                        } else if (typeof marked === 'function') {
                            htmlContent = marked(analysisText);
                        } else {
                            throw new Error('marked API not recognized');
                        }
                        
                        // Render as markdown with better styling
                        content.innerHTML = htmlContent;
                        content.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segue UI", Roboto, sans-serif';
                        content.style.lineHeight = '1.6';
                        content.style.whiteSpace = 'normal';
                        console.log('✅ File markdown rendered successfully');
                    } else {
                        throw new Error('marked library not loaded');
                    }
                } catch (error) {
                    console.warn('⚠️ File markdown rendering failed:', error);
                    // Fallback to plain text if marked is not available
                    content.innerHTML = '';
                    content.textContent = analysisText;
                }
            }
        }
        
        function downloadResult(type) {
            let content, filename;
            if (type === 'transcript') {
                content = currentResults.transcript;
                filename = (currentResults.video_title || 'transcript') + '_transcript.txt';
            } else if (type === 'quotes') {
                content = currentResults.quotes.join('\\n\\n');
                filename = (currentResults.video_title || 'quotes') + '_quotes.txt';
            } else if (type === 'analysis') {
                content = currentResults.analysis;
                filename = (currentResults.video_title || 'analysis') + '_analysis.txt';
            }
            
            if (!content) {
                alert('No content to download!');
                return;
            }
            
            const blob = new Blob([content], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            stopLogUpdates();
        });
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())

    def serve_status(self):
        response = {'status': self.app_state['status'], 'processing': self.app_state['processing']}
        self.send_json_response(response)

    def serve_results(self):
        response = {
            'transcript': self.app_state['transcript'],
            'quotes': self.app_state['quotes'],
            'analysis': self.app_state['analysis'],
            'video_title': self.app_state['video_title']
        }
        self.send_json_response(response)

    def serve_logs(self):
        # Get recent logs from the log capture
        log_contents = log_capture_string.getvalue()
        log_lines = log_contents.strip().split('\n') if log_contents.strip() else []
        
        # Parse logs into structured format
        logs = []
        for line in log_lines[-100:]:  # Last 100 log entries
            if line.strip():
                try:
                    # Parse log format: timestamp - level - message
                    parts = line.split(' - ', 2)
                    if len(parts) >= 3:
                        logs.append({
                            'timestamp': parts[0],
                            'level': parts[1],
                            'message': parts[2]
                        })
                    else:
                        logs.append({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'level': 'INFO',
                            'message': line
                        })
                except:
                    logs.append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'level': 'INFO',
                        'message': line
                    })
        
        self.send_json_response({'logs': logs})

    def serve_settings(self):
        logger.info(f"🔍 Serving settings")
        logger.info(f"🔍 Transcription model: {self.app_state['transcription_model']}")
        logger.info(f"🔍 Quote extraction model: {self.app_state['quote_extraction_model']}")
        logger.info(f"🔍 Analysis model: {self.app_state['analysis_model']}")
        logger.info(f"🔍 Processing type: {self.app_state['processing_type']}")
        
        response = {
            'transcription_model': self.app_state['transcription_model'],
            'quote_extraction_model': self.app_state['quote_extraction_model'],
            'analysis_model': self.app_state['analysis_model'],
            'transcription_prompt': self.app_state['transcription_prompt'],
            'quote_instructions': self.app_state['quote_instructions'],
            'processing_type': self.app_state['processing_type']
        }
        self.send_json_response(response)

    def handle_process_request(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            url = data.get('url', '')
            mode = data['mode']
            timestamps = data.get('timestamps', '')
            user_question = data.get('user_question', '')
            context_before = data.get('context_before', 30)
            context_after = data.get('context_after', 60)
            youtube_method = data.get('youtube_method', 'audio')
            processing_type = data.get('processing_type', 'youtube_audio')
            file_path = data.get('file_path', '')
            
            # Clear previous logs
            log_capture_string.truncate(0)
            log_capture_string.seek(0)
            
            # Validate URL first
            if not validate_url(url):
                logger.error("❌ Invalid YouTube URL provided")
                self.send_json_response({'success': False, 'error': 'Invalid YouTube URL'})
                return
            
            # Set processing state immediately
            self.app_state['processing'] = True
            self.app_state['status'] = 'Starting processing...'
            self.app_state['processing_type'] = processing_type
            
            # Start processing in a separate thread
            processing_thread = threading.Thread(
                target=self._process_in_background,
                args=(url, mode, timestamps, user_question, context_before, context_after, youtube_method, processing_type, file_path)
            )
            processing_thread.daemon = True
            processing_thread.start()
            
            # Return immediately to allow log requests
            self.send_json_response({'success': True, 'message': 'Processing started'})
            
        except Exception as e:
            logger.error(f"❌ Error starting processing: {str(e)}")
            self.app_state['processing'] = False
            self.app_state['status'] = f'Error: {str(e)}'
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_file_process_request(self):
        import tempfile
        import cgi
        try:
            # Parse multipart form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            # Extract form fields
            mode = form.getvalue('mode', 'transcript')
            timestamps = form.getvalue('timestamps', '')
            user_question = form.getvalue('user_question', '')
            context_before = int(form.getvalue('context_before', 30))
            context_after = int(form.getvalue('context_after', 60))
            processing_type = form.getvalue('processing_type', 'local_file')
            
            # Get uploaded file
            file_item = form['file']
            if not file_item.filename:
                self.send_json_response({'success': False, 'error': 'No file uploaded'})
                return
                
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file_item.filename}") as temp_file:
                temp_file.write(file_item.file.read())
                temp_file_path = temp_file.name
            
            logger.info(f"📁 File uploaded: {file_item.filename} -> {temp_file_path}")
            
            # Check if already processing
            if self.app_state['processing']:
                self.send_json_response({'success': False, 'error': 'Already processing another request'})
                return
                
            # Clear previous state
            self.app_state['processing'] = True
            self.app_state['status'] = 'Starting file processing...'
            self.app_state['transcript'] = ''
            self.app_state['quotes'] = []
            self.app_state['analysis'] = ''
            self.app_state['video_title'] = ''
            self.app_state['processing_type'] = processing_type
            
            # Start background processing
            processing_thread = threading.Thread(
                target=self._process_in_background,
                args=('', mode, timestamps, user_question, context_before, context_after, 'audio', processing_type, temp_file_path)
            )
            processing_thread.daemon = True
            processing_thread.start()
            
            self.send_json_response({'success': True})
            
        except Exception as e:
            logger.error(f"❌ Error starting file processing: {str(e)}")
            self.app_state['processing'] = False
            self.app_state['status'] = f'Error: {str(e)}'
            self.send_json_response({'success': False, 'error': str(e)})

    def _process_in_background(self, url, mode, timestamps, user_question, context_before, context_after, youtube_method='audio', processing_type='youtube_audio', file_path=''):
        """Run the actual processing in a background thread"""
        try:
            # Log start of processing
            logger.info("🚀 Starting processing...")
            logger.info(f"🔧 Processing type: {processing_type}")
            logger.info(f"⚙️ Mode: {mode}")
            
            # Store processing type in app state
            self.app_state['processing_type'] = processing_type
            
            transcript = ""
            video_title = ""
            video_description = ""
            
            # Handle different processing types
            if processing_type == 'youtube_captions':
                logger.info(f"📺 Processing YouTube URL with captions: {url}")
                logger.info(f"⚡ Using caption method: {youtube_method}")
                self.app_state['status'] = 'Fetching YouTube captions...'
                
                result = process_youtube_captions(url)
                if not result:
                    logger.error("❌ Failed to process YouTube captions")
                    self.app_state['processing'] = False
                    self.app_state['status'] = 'Failed to process YouTube captions'
                    return
                    
                transcript, _, video_title, video_description = result
                
            elif processing_type == 'youtube_audio':
                logger.info(f"📺 Processing YouTube URL with audio: {url}")
                self.app_state['status'] = 'Downloading and processing video...'
                
                result = process_youtube_url_only(url)
                if not result:
                    logger.error("❌ Failed to process video")
                    self.app_state['processing'] = False
                    self.app_state['status'] = 'Failed to process video'
                    return
                    
                transcript, _, video_title, video_description = result
                
            elif processing_type == 'local_file':
                logger.info(f"📁 Processing local file: {file_path}")
                self.app_state['status'] = 'Processing media file...'
                
                result = process_media_file(file_path)
                if not result:
                    logger.error("❌ Failed to process media file")
                    self.app_state['processing'] = False
                    self.app_state['status'] = 'Failed to process media file'
                    return
                    
                _, transcript, _ = result
                video_title = file_path.split('/')[-1]  # Use filename as title
                video_description = "Local media file"
            self.app_state['transcript'] = transcript
            self.app_state['video_title'] = video_title
            
            logger.info(f"✅ Successfully processed video: {video_title}")
            logger.info(f"📄 Video description: {video_description[:100]}..." if video_description else "📄 No video description available")
            
            quotes = []
            analysis = ""
            
            if mode == 'both' and timestamps:
                self.app_state['status'] = 'Extracting quotes...'
                logger.info("💬 Starting quote extraction...")
                
                if processing_type == 'youtube_captions':
                    success = process_timestamps_from_captions(url, timestamps, context_after, context_before, self.app_state['quote_extraction_model'])
                    if success:
                        logger.info("✅ Quotes extracted from captions successfully")
                        quotes = ["Quotes extracted successfully (see file output)"]
                    else:
                        logger.warning("⚠️ Quote extraction from captions failed")
                elif processing_type == 'local_file':
                    success = process_timestamps_from_file(file_path, timestamps, context_after, context_before, self.app_state['quote_extraction_model'])
                    if success:
                        logger.info("✅ Quotes extracted from file successfully")
                        quotes = ["Quotes extracted successfully (see file output)"]
                    else:
                        logger.warning("⚠️ Quote extraction from file failed")
                else:
                    # Original YouTube audio processing
                    formatted_input = f"{url}\n{timestamps}"
                    _, timestamps_to_process = parse_input(formatted_input)
                    if timestamps_to_process and validate_timestamps_format(timestamps_to_process):
                        quotes = process_timestamps(timestamps_to_process, transcript, context_after, context_before, video_description, self.app_state['quote_extraction_model'])
                        logger.info(f"✅ Extracted {len(quotes)} quotes successfully")
                    else:
                        logger.warning("⚠️ Invalid timestamp format provided")
            elif mode == 'analysis' and user_question:
                self.app_state['status'] = 'Analyzing content...'
                logger.info("🤔 Starting analysis with user question...")
                logger.info(f"📝 User question: {user_question}")
                
                # For all processing types, use the transcript and call process_analysis directly
                logger.info(f"📄 Transcript available: {len(transcript)} chars")
                logger.info(f"📋 Video description available: {len(video_description)} chars")
                
                analysis = process_analysis(transcript, video_description, user_question, self.app_state['analysis_model'])
                
                if analysis:
                    logger.info("✅ Analysis completed successfully!")
                    logger.info(f"📊 Analysis length: {len(analysis)} characters")
                else:
                    logger.warning("⚠️ Analysis failed or returned empty result")
            
            # Update final state
            self.app_state['quotes'] = quotes
            self.app_state['analysis'] = analysis
            self.app_state['processing'] = False
            self.app_state['status'] = 'Completed'
            
            logger.info("🎉 Processing completed successfully!")
            logger.info(f"📊 Final state - Quotes: {len(quotes)}, Analysis: {len(analysis) if analysis else 0} chars")
            
        except Exception as e:
            logger.error(f"❌ Error during background processing: {str(e)}")
            self.app_state['processing'] = False
            self.app_state['status'] = f'Error: {str(e)}'

    def handle_update_settings(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            logger.info(f"🔧 Updating settings with data: {data}")
            
            self.app_state['transcription_model'] = data.get('transcription_model', DEFAULT_SETTINGS['gemini_model'])
            self.app_state['quote_extraction_model'] = data.get('quote_extraction_model', DEFAULT_SETTINGS['gemini_model'])
            self.app_state['analysis_model'] = data.get('analysis_model', DEFAULT_SETTINGS['gemini_model'])
            self.app_state['transcription_prompt'] = data.get('transcription_prompt', TRANSCRIPTION_PROMPT)
            self.app_state['quote_instructions'] = data.get('quote_instructions', QUOTE_EXTRACTION_INSTRUCTIONS.copy())
            
            logger.info(f"🔧 Transcription model: {self.app_state['transcription_model']}")
            logger.info(f"🔧 Quote extraction model: {self.app_state['quote_extraction_model']}")
            logger.info(f"🔧 Analysis model: {self.app_state['analysis_model']}")
            logger.info("⚙️ Advanced settings updated successfully")
            self.send_json_response({'success': True})
            
        except Exception as e:
            logger.error(f"❌ Error updating settings: {str(e)}")
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_clear_request(self):
        try:
            self.app_state['processing'] = False
            self.app_state['status'] = 'Cleared'
            self.app_state['transcript'] = ''
            self.app_state['quotes'] = []
            self.app_state['analysis'] = ''
            self.app_state['video_title'] = ''
            
            # Clear logs
            log_capture_string.truncate(0)
            log_capture_string.seek(0)
            
            logger.info("🗑️ Cleared all data and logs")
            self.send_json_response({'success': True})
            
        except Exception as e:
            logger.error(f"❌ Error clearing data: {str(e)}")
            self.send_json_response({'success': False, 'error': str(e)})

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def start_web_gui(port=8080):
    """Start the web GUI server"""
    try:
        with socketserver.TCPServer(("", port), YouTubeExtractorHandler) as httpd:
            url = f"http://localhost:{port}"
            print(f"🌐 Web GUI running at {url}")
            print("📱 Opening in your default browser...")
            
            # Try multiple methods to open the browser
            def open_browser():
                time.sleep(1.5)
                browser_opened = False
                
                try:
                    # Method 1: Try default browser
                    print("🔍 Attempting to open default browser...")
                    webbrowser.open(url)
                    browser_opened = True
                    print("✅ Browser opened successfully!")
                except Exception as e:
                    print(f"⚠️ Default browser failed: {e}")
                
                if not browser_opened:
                    try:
                        # Method 2: Try specific browsers
                        print("🔍 Trying alternative browsers...")
                        browsers = ['chrome', 'firefox', 'safari', 'opera']
                        for browser_name in browsers:
                            try:
                                browser = webbrowser.get(browser_name)
                                browser.open(url)
                                print(f"✅ Opened with {browser_name}!")
                                browser_opened = True
                                break
                            except:
                                continue
                    except Exception as e:
                        print(f"⚠️ Alternative browsers failed: {e}")
                
                if not browser_opened:
                    print("❌ Could not automatically open browser.")
                    print(f"🔗 Please manually open: {url}")
                    print("💡 Copy and paste this URL into your browser:")
                    print(f"   {url}")
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            print("=" * 60)
            print("🚀 Server is running! Waiting for connections...")
            print(f"🔗 Manual URL: {url}")
            print("⌨️  Press Ctrl+C to stop the server")
            print("=" * 60)
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n👋 Shutting down web server...")
                httpd.shutdown()
                
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use.")
            print("💡 Trying alternative ports...")
            # Try alternative ports
            for alt_port in [8081, 8082, 8083, 8084, 8085]:
                try:
                    with socketserver.TCPServer(("", alt_port), YouTubeExtractorHandler) as httpd:
                        url = f"http://localhost:{alt_port}"
                        print(f"✅ Found available port: {alt_port}")
                        print(f"🌐 Web GUI running at {url}")
                        
                        def open_browser_alt():
                            time.sleep(1.5)
                            try:
                                webbrowser.open(url)
                                print("✅ Browser opened!")
                            except:
                                print(f"🔗 Please manually open: {url}")
                        
                        threading.Thread(target=open_browser_alt, daemon=True).start()
                        print(f"🔗 Manual URL: {url}")
                        print("⌨️  Press Ctrl+C to stop the server")
                        
                        try:
                            httpd.serve_forever()
                        except KeyboardInterrupt:
                            print("\n👋 Shutting down web server...")
                            httpd.shutdown()
                        return
                except OSError:
                    continue
            
            print("❌ Could not find an available port. Please try later.")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='YouTube Quote Extractor Web GUI')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the web server on (default: 8080)')
    
    args = parser.parse_args()
    start_web_gui(args.port)


if __name__ == "__main__":
    main() 