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

# Global log capture - Set up BEFORE importing other modules
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

# Now import our modules - they will use the logging configuration we just set up
from config import DEFAULT_SETTINGS, QUOTE_EXTRACTION_INSTRUCTIONS, TRANSCRIPTION_PROMPT
from main import (
    validate_url, validate_timestamps_format, parse_input,
    process_youtube_url_only, process_timestamps
)

logger = logging.getLogger(__name__)


class YouTubeExtractorHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.app_state = {
            'processing': False,
            'status': 'Ready',
            'transcript': '',
            'quotes': [],
            'video_title': '',
            'gemini_model': DEFAULT_SETTINGS['gemini_model'],
            'transcription_prompt': TRANSCRIPTION_PROMPT,
            'quote_instructions': QUOTE_EXTRACTION_INSTRUCTIONS.copy()
        }
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
            <button class="tab active" onclick="showMainTab('main')">📝 Main</button>
            <button class="tab" onclick="showMainTab('advanced')">⚙️ Advanced</button>
            <button class="tab" onclick="showMainTab('logs')">📊 Live Logs</button>
        </div>

        <!-- Main Tab -->
        <div class="tab-content active" id="main-tab">
            <div class="section">
                <h3>1. YouTube URL</h3>
                <input type="url" id="url" placeholder="Enter YouTube URL here..." />
            </div>

            <div class="section">
                <h3>2. Processing Mode</h3>
                <div class="radio-group">
                    <div class="radio-item">
                        <input type="radio" id="transcript-only" name="mode" value="transcript" />
                        <label for="transcript-only">Generate Transcript Only</label>
                    </div>
                    <div class="radio-item">
                        <input type="radio" id="transcript-quotes" name="mode" value="both" checked />
                        <label for="transcript-quotes">Generate Transcript + Extract Quotes</label>
                    </div>
                </div>
            </div>

            <div class="section" id="quote-settings">
                <h3>3. Context Settings</h3>
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
                <h3>4. Timestamps</h3>
                <p style="color: #666; margin-bottom: 10px;">Enter timestamps (MM:SS or HH:MM:SS) one per line:</p>
                <textarea id="timestamps" placeholder="1:30 - Discussion about AI&#10;2:45 - Important quote&#10;5:20 - Key insight"></textarea>
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
                </div>
                <div class="result-content" id="result-content"></div>
                <div style="margin-top: 15px;">
                    <button class="btn-secondary" onclick="downloadResult('transcript')">💾 Download Transcript</button>
                    <button class="btn-secondary" id="download-quotes-btn" onclick="downloadResult('quotes')">💾 Download Quotes</button>
                </div>
            </div>
        </div>

        <!-- Advanced Tab -->
        <div class="tab-content" id="advanced-tab">
            <div class="advanced-section">
                <h3>🤖 AI Model Settings</h3>
                <div class="section">
                    <label for="gemini-model">Gemini Model:</label>
                    <select id="gemini-model">
                        <option value="gemini-2.5-flash" selected>gemini-2.5-flash (Default)</option>
                        <option value="gemini-2.5-pro">gemini-2.5-pro</option>
                        <option value="gemini-2.5-flash-lite-preview-06-17">gemini-2.5-flash-lite-preview-06-17</option>
                        <option value="gemini-2.0-flash">gemini-2.0-flash</option>
                        <option value="gemini-2.0-flash-lite">gemini-2.0-flash-lite</option>
                        <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                        <option value="gemini-1.5-flash-8b">gemini-1.5-flash-8b</option>
                        <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                    </select>
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
        let currentResults = { transcript: '', quotes: [], video_title: '' };
        let currentTab = 'transcript';
        let currentMainTab = 'main';
        let logUpdateInterval;
        
        // Initialize advanced settings after a short delay
        setTimeout(function() {
            loadAdvancedSettings();
        }, 100);
        
        // Toggle quote settings based on mode
        document.querySelectorAll('input[name="mode"]').forEach(radio => {
            radio.addEventListener('change', function() {
                const quoteSettings = document.getElementById('quote-settings');
                const timestampsSection = document.getElementById('timestamps-section');
                if (this.value === 'transcript') {
                    quoteSettings.classList.add('hidden');
                    timestampsSection.classList.add('hidden');
                } else {
                    quoteSettings.classList.remove('hidden');
                    timestampsSection.classList.remove('hidden');
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
                    document.getElementById('gemini-model').value = data.gemini_model;
                    document.getElementById('transcription-prompt').value = data.transcription_prompt;
                    
                    // Load quote instructions as text
                    document.getElementById('quote-instructions').value = data.quote_instructions.join('\\n');
                })
                .catch(error => {
                    console.error('Error loading settings:', error);
                });
        }
        
        function saveAdvancedSettings() {
            const geminiModel = document.getElementById('gemini-model').value;
            const transcriptionPrompt = document.getElementById('transcription-prompt').value;
            const quoteInstructionsText = document.getElementById('quote-instructions').value;
            
            // Split by lines and filter out empty lines
            const instructions = quoteInstructionsText.split('\\n')
                .map(line => line.trim())
                .filter(line => line.length > 0);
            
            const settings = {
                gemini_model: geminiModel,
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
            
            document.getElementById('process-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
            document.getElementById('status').textContent = 'Processing...';
            
            // Switch to logs tab automatically to show progress
            showMainTab('logs');
            
            const data = {
                url: url,
                mode: mode,
                timestamps: timestamps,
                context_before: parseInt(contextBefore),
                context_after: parseInt(contextAfter)
            };
            
            fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(response => response.json())
              .then(result => {
                  if (result.success) {
                      currentResults = result.data;
                      showResults();
                      document.getElementById('status').textContent = 'Processing completed successfully!';
                      // Switch back to main tab to show results
                      showMainTab('main');
                  } else {
                      alert('Error: ' + result.error);
                      document.getElementById('status').textContent = 'Error: ' + result.error;
                  }
                  processingComplete();
              }).catch(error => {
                  alert('Error: ' + error);
                  document.getElementById('status').textContent = 'Error: ' + error;
                  processingComplete();
              });
        }
        
        function stopProcessing() {
            fetch('/api/clear', { method: 'POST' });
            processingComplete();
            document.getElementById('status').textContent = 'Processing stopped';
        }
        
        function processingComplete() {
            document.getElementById('process-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;
        }
        
        function clearAll() {
            document.getElementById('url').value = '';
            document.getElementById('timestamps').value = '';
            document.getElementById('results').classList.add('hidden');
            currentResults = { transcript: '', quotes: [], video_title: '' };
            document.getElementById('status').textContent = 'Cleared all fields';
        }
        
        function showResults() {
            document.getElementById('results').classList.remove('hidden');
            document.getElementById('quotes-tab').style.display = currentResults.quotes.length > 0 ? 'block' : 'none';
            document.getElementById('download-quotes-btn').style.display = currentResults.quotes.length > 0 ? 'inline-block' : 'none';
            showResultTab('transcript');
        }
        
        function showResultTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.result-tab').forEach(t => t.classList.remove('active'));
            document.querySelector('[onclick="showResultTab(\\'' + tab + '\\')"]').classList.add('active');
            
            const content = document.getElementById('result-content');
            if (tab === 'transcript') {
                content.textContent = currentResults.transcript || 'No transcript available';
            } else {
                content.textContent = currentResults.quotes.join('\\n\\n') || 'No quotes available';
            }
        }
        
        function downloadResult(type) {
            let content, filename;
            if (type === 'transcript') {
                content = currentResults.transcript;
                filename = (currentResults.video_title || 'transcript') + '_transcript.txt';
            } else {
                content = currentResults.quotes.join('\\n\\n');
                filename = (currentResults.video_title || 'quotes') + '_quotes.txt';
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
        response = {
            'gemini_model': self.app_state['gemini_model'],
            'transcription_prompt': self.app_state['transcription_prompt'],
            'quote_instructions': self.app_state['quote_instructions']
        }
        self.send_json_response(response)

    def handle_process_request(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            url = data['url']
            mode = data['mode']
            timestamps = data.get('timestamps', '')
            context_before = data.get('context_before', 30)
            context_after = data.get('context_after', 60)
            
            # Clear previous logs
            log_capture_string.truncate(0)
            log_capture_string.seek(0)
            
            # Log start of processing
            logger.info("🚀 Starting YouTube Quote Extractor")
            logger.info(f"📺 Processing URL: {url}")
            logger.info(f"⚙️ Mode: {mode}")
            
            # Validate URL
            if not validate_url(url):
                logger.error("❌ Invalid YouTube URL provided")
                self.send_json_response({'success': False, 'error': 'Invalid YouTube URL'})
                return
            
            self.app_state['processing'] = True
            self.app_state['status'] = 'Processing...'
            
            # Process video
            logger.info("🎵 Downloading and processing video...")
            result = process_youtube_url_only(url)
            if not result:
                logger.error("❌ Failed to process video")
                self.send_json_response({'success': False, 'error': 'Failed to process video'})
                return
                
            transcript, _, video_title, video_description = result
            self.app_state['transcript'] = transcript
            self.app_state['video_title'] = video_title
            
            logger.info(f"✅ Successfully processed video: {video_title}")
            logger.info(f"📄 Video description: {video_description[:100]}..." if video_description else "📄 No video description available")
            
            quotes = []
            if mode == 'both' and timestamps:
                logger.info("💬 Starting quote extraction...")
                # Format the input properly for parse_input function
                formatted_input = f"{url}\n{timestamps}"
                _, timestamps_to_process = parse_input(formatted_input)
                if timestamps_to_process and validate_timestamps_format(timestamps_to_process):
                    quotes = process_timestamps(timestamps_to_process, transcript, context_after, context_before, video_description)
                    logger.info(f"✅ Extracted {len(quotes)} quotes successfully")
                else:
                    logger.warning("⚠️ Invalid timestamp format provided")
            
            self.app_state['quotes'] = quotes
            self.app_state['processing'] = False
            self.app_state['status'] = 'Completed'
            
            logger.info("🎉 Processing completed successfully!")
            
            response_data = {
                'transcript': transcript,
                'quotes': quotes,
                'video_title': video_title
            }
            
            self.send_json_response({'success': True, 'data': response_data})
            
        except Exception as e:
            logger.error(f"❌ Error processing request: {str(e)}")
            self.app_state['processing'] = False
            self.app_state['status'] = f'Error: {str(e)}'
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_update_settings(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            self.app_state['gemini_model'] = data.get('gemini_model', DEFAULT_SETTINGS['gemini_model'])
            self.app_state['transcription_prompt'] = data.get('transcription_prompt', TRANSCRIPTION_PROMPT)
            self.app_state['quote_instructions'] = data.get('quote_instructions', QUOTE_EXTRACTION_INSTRUCTIONS.copy())
            
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
            print(f"🌐 Web GUI running at http://localhost:{port}")
            print("📱 Opening in your default browser...")
            
            # Open browser after a short delay
            def open_browser():
                time.sleep(1.5)
                webbrowser.open(f'http://localhost:{port}')
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n👋 Shutting down web server...")
                httpd.shutdown()
                
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use. Try a different port.")
            print(f"   Example: python {__file__} --port 8081")
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