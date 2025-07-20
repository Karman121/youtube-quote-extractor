#!/usr/bin/env python3
"""
YouTube Auto-Caption Processor
Fetches auto-generated captions from YouTube videos for transcription,
quote extraction, and analysis
"""

import os
import sys
import re
import logging
import yt_dlp
from typing import Optional, Tuple, Dict
from main import process_analysis, save_quotes
from transcript_utils import (
    extract_timestamps_and_descriptions, get_transcript_segment
)
from quote_extraction import extract_quote_with_gemini
from utils import sanitize_filename
from config import DEFAULT_SETTINGS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_video_info(youtube_url: str) -> Optional[Dict]:
    """Get video information without downloading."""
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return {
                'title': info.get('title', 'Unknown Video'),
                'description': info.get('description', ''),
                'duration': info.get('duration', 0),
                'subtitles': info.get('subtitles', {}),
                'automatic_captions': info.get('automatic_captions', {})
            }
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return None


def fetch_auto_captions(
    youtube_url: str, output_dir: str = "."
) -> Optional[Tuple[str, str, str, str]]:
    """
    Fetch auto-generated captions from YouTube.
    Returns (caption_file, title, description, video_url)
    """
    print("🔍 Fetching video information...")
    
    video_info = get_video_info(youtube_url)
    if not video_info:
        print("❌ Failed to get video information")
        return None
    
    title = video_info['title']
    description = video_info['description']
    
    print(f"📹 Video: {title}")
    
    # Check for available captions
    auto_captions = video_info.get('automatic_captions', {})
    manual_captions = video_info.get('subtitles', {})
    
    # Prefer manual captions over auto-captions
    captions_source = None
    if manual_captions:
        print("✅ Found manual captions")
        captions_source = manual_captions
        caption_type = "manual"
    elif auto_captions:
        print("✅ Found auto-generated captions")
        captions_source = auto_captions
        caption_type = "auto"
    else:
        print("❌ No captions available for this video")
        return None
    
    # Look for English captions first
    lang_options = ['en', 'en-US', 'en-GB']
    selected_lang = None
    
    for lang in lang_options:
        if lang in captions_source:
            selected_lang = lang
            break
    
    if not selected_lang:
        # If no English, take the first available language
        available_langs = list(captions_source.keys())
        if available_langs:
            selected_lang = available_langs[0]
            print(f"⚠️ No English captions found, using: {selected_lang}")
        else:
            print("❌ No caption languages available")
            return None
    
    print(f"🔤 Using {caption_type} captions in language: {selected_lang}")
    
    # Generate output filename
    sanitized_title = sanitize_filename(title)
    caption_filename = f"{sanitized_title}_captions.vtt"
    caption_path = os.path.join(output_dir, caption_filename)
    
    # Check if captions already exist
    if os.path.exists(caption_path):
        print(f"📄 Found existing captions: {caption_filename}")
        return caption_path, title, description, youtube_url
    
    # Download captions
    print("⬇️ Downloading captions...")
    
    try:
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True if caption_type == "auto" else False,
            'skip_download': True,  # Don't download video
            'subtitleslangs': [selected_lang],
            'subtitlesformat': 'vtt',  # WebVTT format
            'outtmpl': os.path.join(output_dir, f"{sanitized_title}.%(ext)s"),
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        # Look for the generated caption file
        expected_files = [
            os.path.join(output_dir, f"{sanitized_title}.{selected_lang}.vtt"),
            os.path.join(output_dir, f"{sanitized_title}.en.vtt"),
            caption_path
        ]
        
        for file_path in expected_files:
            if os.path.exists(file_path):
                if file_path != caption_path:
                    # Rename to our expected filename
                    os.rename(file_path, caption_path)
                print(f"✅ Captions downloaded: {caption_filename}")
                return caption_path, title, description, youtube_url
        
        print("❌ Caption file not found after download")
        return None
        
    except Exception as e:
        logger.error(f"Failed to download captions: {e}")
        print(f"❌ Failed to download captions: {e}")
        return None


def parse_vtt_to_transcript(vtt_file: str) -> str:
    """
    Parse WebVTT caption file to transcript format.
    Converts to [MM:SS] Speaker: Text format with deduplication.
    """
    try:
        with open(vtt_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read VTT file: {e}")
        return ""
    
    caption_entries = []
    
    # Split into blocks
    blocks = re.split(r'\n\n+', content)
    
    for block in blocks:
        block = block.strip()
        if not block or block.startswith('WEBVTT') or block.startswith('NOTE'):
            continue
        
        lines = block.split('\n')
        if len(lines) < 2:
            continue
        
        # Look for timestamp line (format: 00:00:10.500 --> 00:00:13.500)
        timestamp_line = None
        text_lines = []
        
        for line in lines:
            if '-->' in line:
                timestamp_line = line
            elif line.strip() and not line.strip().isdigit():
                # Remove HTML tags and clean text
                clean_text = re.sub(r'<[^>]+>', '', line)
                clean_text = clean_text.strip()
                if clean_text:
                    text_lines.append(clean_text)
        
        if timestamp_line and text_lines:
            # Extract start time
            time_match = re.match(
                r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})', timestamp_line
            )
            if time_match:
                hours = int(time_match.group(1))
                minutes = int(time_match.group(2))
                seconds = int(time_match.group(3))
                
                # Convert to total seconds for sorting
                total_seconds = hours * 3600 + minutes * 60 + seconds
                
                # Combine text lines
                text = ' '.join(text_lines)
                
                caption_entries.append((total_seconds, text))
    
    # Sort by timestamp and deduplicate
    caption_entries.sort(key=lambda x: x[0])
    
    # Merge overlapping/redundant captions
    merged_captions = []
    prev_text = ""
    
    for timestamp_sec, text in caption_entries:
        # Skip if this text is completely contained in previous text
        if text in prev_text:
            continue
        
        # Check if this is an extension of previous text
        if prev_text and text.startswith(prev_text):
            # Replace the last entry with the extended version
            if merged_captions:
                merged_captions[-1] = (timestamp_sec, text)
            else:
                merged_captions.append((timestamp_sec, text))
        else:
            # New text segment
            merged_captions.append((timestamp_sec, text))
        
        prev_text = text
    
    # Convert to transcript format
    transcript_lines = []
    for timestamp_sec, text in merged_captions:
        # Convert back to MM:SS format
        total_minutes = timestamp_sec // 60
        seconds = timestamp_sec % 60
        timestamp = f"[{total_minutes:02d}:{seconds:02d}]"
        
        # Add timestamp and text without speaker label
        transcript_lines.append(f"{timestamp} {text}")
    
    return '\n'.join(transcript_lines)


def process_youtube_captions(youtube_url: str, progress_callback=None) -> Optional[Tuple[str, str, str, str]]:
    """
    Process YouTube video using auto-captions.
    Returns (transcript, transcript_filename, title, description)
    """
    if progress_callback:
        progress_callback("Fetching captions...")
    
    # Fetch captions
    result = fetch_auto_captions(youtube_url)
    if not result:
        return None
    
    caption_file, title, description, video_url = result
    
    if progress_callback:
        progress_callback("Converting captions to transcript...")
    
    # Convert to transcript format
    transcript = parse_vtt_to_transcript(caption_file)
    if not transcript:
        print("❌ Failed to parse captions to transcript")
        return None
    
    # Save transcript
    sanitized_title = sanitize_filename(title)
    transcript_filename = f"{sanitized_title}_transcript_captions.txt"
    
    try:
        with open(transcript_filename, 'w', encoding='utf-8') as f:
            f.write(transcript)
        print(f"💾 Transcript saved: {transcript_filename}")
        print(f"📄 Length: {len(transcript)} characters")
    except Exception as e:
        logger.error(f"Failed to save transcript: {e}")
        return None
    
    if progress_callback:
        progress_callback("Complete!")
    
    return transcript, transcript_filename, title, description


def process_timestamps_from_captions(
    youtube_url: str, 
    timestamps_input: str,
    context_after: int = None,
    context_before: int = None,
    gemini_model: str = None
) -> bool:
    """
    Process YouTube video captions with specific timestamps for quote extraction.
    """
    print("🎬 YouTube Caption-based Quote Extractor")
    print("=" * 50)
    
    # Parse timestamps
    timestamps_to_process = extract_timestamps_and_descriptions(timestamps_input)
    if not timestamps_to_process:
        print("[ERROR] No timestamps found in input")
        return False
    
    # Process the video captions
    result = process_youtube_captions(youtube_url)
    if not result:
        return False
    
    full_transcript, transcript_filename, title, description = result
    
    # Use default context if not provided
    if context_after is None:
        context_after = DEFAULT_SETTINGS["default_context_after_seconds"]
    if context_before is None:
        context_before = DEFAULT_SETTINGS["default_context_before_seconds"]
    
    print(f"📄 Processing {len(timestamps_to_process)} timestamps...")
    print(f"⏱️ Context: {context_before}s before, {context_after}s after")
    
    # Process each timestamp
    extracted_quotes = {}
    for i, ts_info in enumerate(timestamps_to_process):
        try:
            print(f"Processing timestamp {i+1}/{len(timestamps_to_process)}: {ts_info.timestamp}")
            
            # Get transcript segment
            segment = get_transcript_segment(
                full_transcript, i, timestamps_to_process, 
                context_after, context_before
            )
            
            if not segment:
                print(f"⚠️ No transcript segment found for {ts_info.timestamp}")
                continue
            
            # Extract quote
            quote = extract_quote_with_gemini(
                segment, ts_info.timestamp, 
                video_description=description,
                user_description=ts_info.description,
                gemini_model=gemini_model
            )
            
            extracted_quotes[ts_info.timestamp] = quote
            print(f"✅ Quote extracted for {ts_info.timestamp}")
            
        except Exception as e:
            logger.error(f"Failed to process timestamp {ts_info.timestamp}: {e}")
            print(f"❌ Failed to extract quote for {ts_info.timestamp}: {e}")
    
    if extracted_quotes:
        # Save quotes
        save_quotes(extracted_quotes, title)
        print(f"\n🎉 Successfully extracted {len(extracted_quotes)} quotes!")
        return True
    else:
        print("\n❌ No quotes were extracted.")
        return False


def analyze_youtube_captions(youtube_url: str, question: str, gemini_model: str = None) -> bool:
    """
    Analyze YouTube video captions by asking a question about the content.
    """
    print("🤔 YouTube Caption Analysis Mode")
    print("=" * 50)
    
    # Process the video captions
    result = process_youtube_captions(youtube_url)
    if not result:
        return False
    
    full_transcript, transcript_filename, title, description = result
    
    print(f"📝 Question: {question}")
    print("🧠 Analyzing content...")
    
    # Analyze using existing function
    analysis_result = process_analysis(
        transcript=full_transcript,
        video_description=description,
        user_question=question,
        gemini_model=gemini_model
    )
    
    if analysis_result:
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULT")
        print("="*60)
        print(analysis_result)
        print("="*60)
        
        # Save analysis to file
        sanitized_title = sanitize_filename(title)
        analysis_filename = f"{sanitized_title}_analysis_captions.txt"
        try:
            with open(analysis_filename, 'w', encoding='utf-8') as f:
                f.write(f"Video: {title}\n")
                f.write(f"URL: {youtube_url}\n")
                f.write(f"Question: {question}\n\n")
                f.write("Analysis:\n")
                f.write(analysis_result)
            print(f"\n💾 Analysis saved to: {analysis_filename}")
        except Exception as e:
            logger.warning(f"Failed to save analysis: {e}")
        
        return True
    else:
        print("❌ Analysis failed")
        return False


def main():
    """Main function for command-line usage."""
    print("🎬 YouTube Auto-Caption Processor")
    print("Process YouTube videos using auto-generated captions")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python youtube_captions.py <youtube_url> [mode]")
        print("")
        print("Modes:")
        print("  transcript - Just generate transcript from captions (default)")
        print("  quotes - Extract quotes from timestamps")
        print("  analyze - Ask questions about the content")
        print("")
        print("Examples:")
        print("  python youtube_captions.py https://youtube.com/watch?v=...")
        print("  python youtube_captions.py https://youtube.com/watch?v=... quotes")
        print("  python youtube_captions.py https://youtube.com/watch?v=... analyze")
        return
    
    youtube_url = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "transcript"
    
    if mode == "transcript":
        result = process_youtube_captions(youtube_url)
        if result:
            transcript, transcript_filename, title, description = result
            print(f"\n✅ Transcript generated from captions: {transcript_filename}")
            print(f"🎬 Video: {title}")
        else:
            print("❌ Failed to generate transcript from captions")
    
    elif mode == "quotes":
        print("\nEnter timestamps for quote extraction (format: MM:SS - description)")
        print("End with an empty line:")
        
        timestamps_input = ""
        while True:
            line = input().strip()
            if not line:
                break
            timestamps_input += line + "\n"
        
        if timestamps_input.strip():
            process_timestamps_from_captions(youtube_url, timestamps_input)
        else:
            print("No timestamps provided")
    
    elif mode == "analyze":
        question = input("\nEnter your question about the content: ").strip()
        if question:
            analyze_youtube_captions(youtube_url, question)
        else:
            print("No question provided")
    
    else:
        print(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main() 