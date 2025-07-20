#!/usr/bin/env python3
"""
File-based Quote Extractor
Processes local audio/video files for transcription, quote extraction, 
and analysis
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from transcript_utils import (
    transcribe_audio_with_chunking, 
    extract_timestamps_and_descriptions, get_transcript_segment
)
from quote_extraction import extract_quote_with_gemini
from main import process_analysis, save_quotes
from utils import sanitize_filename
from config import DEFAULT_SETTINGS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supported file extensions
AUDIO_EXTENSIONS = {
    '.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma'
}
VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'
}


def find_ffmpeg_executable() -> Optional[str]:
    """Find ffmpeg executable in bundled directory or system PATH."""
    # Check bundled ffmpeg first
    bundled_ffmpeg = None
    if sys.platform.startswith('win'):
        bundled_ffmpeg = os.path.join('ffmpeg', 'ffmpeg.exe')
    else:
        bundled_ffmpeg = os.path.join('ffmpeg', 'ffmpeg')
    
    if os.path.exists(bundled_ffmpeg):
        logger.info(f"Using bundled ffmpeg: {bundled_ffmpeg}")
        return bundled_ffmpeg
    
    # Check system PATH
    try:
        result = subprocess.run(
            ['which', 'ffmpeg'], capture_output=True, text=True
        )
        if result.returncode == 0:
            system_ffmpeg = result.stdout.strip()
            logger.info(f"Using system ffmpeg: {system_ffmpeg}")
            return system_ffmpeg
    except FileNotFoundError:
        pass
    
    # Try direct call (Windows)
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        logger.info("Using system ffmpeg from PATH")
        return 'ffmpeg'
    except FileNotFoundError:
        pass
    
    logger.error(
        "ffmpeg not found. Please install ffmpeg or ensure it's in your PATH."
    )
    return None


def validate_file(file_path: str) -> Tuple[bool, str, str]:
    """
    Validate if file exists and determine its type.
    Returns (is_valid, file_type, error_message)
    """
    if not os.path.exists(file_path):
        return False, "", f"File not found: {file_path}"
    
    if not os.path.isfile(file_path):
        return False, "", f"Path is not a file: {file_path}"
    
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext in AUDIO_EXTENSIONS:
        return True, "audio", ""
    elif file_ext in VIDEO_EXTENSIONS:
        return True, "video", ""
    else:
        supported = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS
        return False, "", f"Unsupported file format: {file_ext}. Supported: {supported}"


def convert_video_to_audio(video_path: str, output_path: str = None) -> Optional[str]:
    """
    Convert video file to audio using ffmpeg.
    Returns path to the audio file or None if failed.
    """
    ffmpeg_path = find_ffmpeg_executable()
    if not ffmpeg_path:
        return None
    
    if output_path is None:
        # Generate output path in same directory as video
        video_path_obj = Path(video_path)
        output_path = str(video_path_obj.with_suffix('.mp3'))
    
    # Check if audio file already exists
    if os.path.exists(output_path):
        logger.info(f"Audio file already exists: {output_path}")
        return output_path
    
    logger.info(f"Converting video to audio: {video_path} -> {output_path}")
    
    try:
        # FFmpeg command to extract audio
        cmd = [
            ffmpeg_path,
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'mp3',
            '-ab', f"{DEFAULT_SETTINGS['audio_quality']}k",
            '-ar', '44100',  # Standard sample rate
            '-y',  # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully converted to audio: {output_path}")
            return output_path
        else:
            logger.error(f"ffmpeg failed: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error during video conversion: {e}")
        return None

def process_media_file(file_path: str, progress_callback=None) -> Optional[Tuple[str, str, str]]:
    """
    Process a local media file and return (audio_path, transcript, filename).
    """
    if progress_callback:
        progress_callback("Validating file...")
    
    # Validate file
    is_valid, file_type, error_msg = validate_file(file_path)
    if not is_valid:
        logger.error(error_msg)
        print(f"[ERROR] {error_msg}")
        return None
    
    logger.info(f"Processing {file_type} file: {file_path}")
    
    # Get audio file path
    audio_path = file_path
    if file_type == "video":
        if progress_callback:
            progress_callback("Converting video to audio...")
        
        audio_path = convert_video_to_audio(file_path)
        if not audio_path:
            logger.error("Failed to convert video to audio")
            print("[ERROR] Failed to convert video to audio")
            return None
    
    # Generate transcript filename
    file_stem = Path(file_path).stem
    sanitized_name = sanitize_filename(file_stem)
    transcript_filename = f"{sanitized_name}_transcript.txt"
    
    # Check if transcript already exists
    if os.path.exists(transcript_filename):
        logger.info(f"Found existing transcript: {transcript_filename}")
        try:
            with open(transcript_filename, 'r', encoding='utf-8') as f:
                transcript = f.read()
            if progress_callback:
                progress_callback("Using existing transcript...")
            return audio_path, transcript, transcript_filename
        except Exception as e:
            logger.warning(f"Failed to read existing transcript: {e}")
    
    if progress_callback:
        progress_callback("Generating transcript...")
    
    # Transcribe audio
    try:
        transcript = transcribe_audio_with_chunking(audio_path, transcript_filename)
        if not transcript:
            logger.error("Transcription failed - empty result")
            print("[ERROR] Transcription failed")
            return None
        
        logger.info(f"Transcription completed: {len(transcript)} characters")
        if progress_callback:
            progress_callback("Transcription complete!")
        
        return audio_path, transcript, transcript_filename
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        print(f"[ERROR] Transcription failed: {e}")
        return None

def process_timestamps_from_file(
    file_path: str, 
    timestamps_input: str,
    context_after: int = None,
    context_before: int = None,
    gemini_model: str = None
) -> bool:
    """
    Process a media file with specific timestamps for quote extraction.
    """
    print("🎬 File-based Quote Extractor")
    print("=" * 50)
    
    # Parse timestamps
    timestamps_to_process = extract_timestamps_and_descriptions(timestamps_input)
    if not timestamps_to_process:
        print(f"[ERROR] No timestamps found in input")
        return False
    
    # Process the media file
    result = process_media_file(file_path)
    if not result:
        return False
    
    audio_path, full_transcript, transcript_filename = result
    
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
                video_description="Local media file",  # No description available for local files
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
        file_stem = Path(file_path).stem
        save_quotes(extracted_quotes, file_stem)
        print(f"\n🎉 Successfully extracted {len(extracted_quotes)} quotes!")
        return True
    else:
        print("\n❌ No quotes were extracted.")
        return False

def analyze_file(file_path: str, question: str, gemini_model: str = None) -> bool:
    """
    Analyze a media file by asking a question about its content.
    """
    print("🤔 File Analysis Mode")
    print("=" * 50)
    
    # Process the media file
    result = process_media_file(file_path)
    if not result:
        return False
    
    audio_path, full_transcript, transcript_filename = result
    
    print(f"📝 Question: {question}")
    print("🧠 Analyzing content...")
    
    # Analyze using existing function
    analysis_result = process_analysis(
        transcript=full_transcript,
        video_description="Local media file",  # No description for local files
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
        file_stem = Path(file_path).stem
        analysis_filename = f"{sanitize_filename(file_stem)}_analysis.txt"
        try:
            with open(analysis_filename, 'w', encoding='utf-8') as f:
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
    print("🎬 File-based Quote Extractor")
    print("Process local audio/video files for transcription and quote extraction")
    print("=" * 70)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python file_processor.py <file_path> [mode]")
        print("")
        print("Modes:")
        print("  transcript - Just generate transcript (default)")
        print("  quotes - Extract quotes from timestamps")
        print("  analyze - Ask questions about the content")
        print("")
        print("Examples:")
        print("  python file_processor.py video.mp4")
        print("  python file_processor.py audio.mp3 quotes")
        print("  python file_processor.py video.mp4 analyze")
        return
    
    file_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "transcript"
    
    if mode == "transcript":
        result = process_media_file(file_path)
        if result:
            audio_path, transcript, transcript_filename = result
            print(f"\n✅ Transcript generated: {transcript_filename}")
            print(f"📄 Length: {len(transcript)} characters")
        else:
            print("❌ Failed to generate transcript")
    
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
            process_timestamps_from_file(file_path, timestamps_input)
        else:
            print("No timestamps provided")
    
    elif mode == "analyze":
        question = input("\nEnter your question about the content: ").strip()
        if question:
            analyze_file(file_path, question)
        else:
            print("No question provided")
    
    else:
        print(f"Unknown mode: {mode}")

if __name__ == "__main__":
    main() 