# =========================
# Imports and Configuration
# =========================
import logging
import os
import re
from typing import List, Optional
from transcript_utils import (
    parse_input, parse_timestamp_to_seconds, get_transcript_segment,
    transcribe_audio_with_chunking, TimestampInfo, sanitize_filename
)
from audio_utils import download_audio
from quote_extraction import extract_quote_with_gemini
from config import (
    DEFAULT_SETTINGS, 
    USER_PROMPTS, 
    ERROR_MESSAGES, 
    SUCCESS_MESSAGES
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =========================
# Core Business Logic Functions (for GUI integration)
# =========================

def validate_url(youtube_url: str) -> bool:
    """Validate YouTube URL only."""
    if not youtube_url:
        logger.error("No YouTube URL provided.")
        return False
    return True


def validate_timestamps_format(timestamps_to_process: List[TimestampInfo]) -> bool:
    """Validate timestamp formats only."""
    for ts_info in timestamps_to_process:
        if not re.match(r'^(\d{1,2}:\d{2})(?::\d{2})?$', ts_info.timestamp):
            logger.error(f"Invalid timestamp format: {ts_info.timestamp}")
            return False
    return True


def validate_input(youtube_url, timestamps_to_process):
    """Validate the parsed input."""
    if not youtube_url:
        print(f"[ERROR] {ERROR_MESSAGES['no_url']}")
        logger.error("No YouTube URL found in input.")
        return False
    
    if not timestamps_to_process:
        print(f"[ERROR] {ERROR_MESSAGES['no_timestamps']}")
        logger.error("No timestamps found in input.")
        return False
    
    # Validate timestamp formats
    if not validate_timestamps_format(timestamps_to_process):
        return False
    
    return True


def process_youtube_url_only(youtube_url: str, progress_callback=None) -> Optional[tuple]:
    """Process YouTube URL for transcript-only mode."""
    if progress_callback:
        progress_callback("Validating URL...")
    
    if not validate_url(youtube_url):
        return None
    
    if progress_callback:
        progress_callback("Downloading audio...")
    
    download_result = download_and_prepare_audio(youtube_url)
    if not download_result:
        return None
    
    audio_file_path, video_title, video_description = download_result
    
    if progress_callback:
        progress_callback("Generating transcript...")
    
    full_transcript, transcript_filename = get_or_create_transcript(audio_file_path, video_title)
    if not full_transcript:
        return None
    
    if progress_callback:
        progress_callback("Complete!")
    
    return full_transcript, transcript_filename, video_title, video_description


# =========================
# Original CLI Functions
# =========================

def extract_timestamps_and_descriptions(text: str) -> List[TimestampInfo]:
    """Extract timestamps and descriptions from text in various formats."""
    # Pattern to match timestamps in various formats
    timestamp_patterns = [
        r'(\d{1,2}:\d{2}(?::\d{2})?)',  # MM:SS or HH:MM:SS
        # With dash/description
        r'(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]?\s*(.*?)(?=\n\d{1,2}:\d{2}|$)',
        # With space/description
        r'(\d{1,2}:\d{2}(?::\d{2})?)\s+(.*?)(?=\n\d{1,2}:\d{2}|$)',
        r'@?(\d{1,2}:\d{2}(?::\d{2})?)',  # With optional @
    ]

    results = []
    lines = text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Try each pattern
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                timestamp = match.group(1)
                # Try to get description if it exists
                description = match.group(2).strip() if len(match.groups()) > 1 else None
                if description:
                    results.append(TimestampInfo(
                        timestamp=timestamp,
                        description=description
                    ))
                else:
                    results.append(TimestampInfo(timestamp=timestamp))
                break

    # Log what we found
    logger.info("=== Extracted Timestamps ===")
    for info in results:
        logger.info(f"Timestamp: {info.timestamp}")
        if info.description:
            logger.info(f"Description: {info.description}")

    return results


def save_transcript_to_file(transcript: str, filename: str):
    """Save transcript to a file."""
    filepath = os.path.join(".", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(transcript)
    logger.info(f"Saved transcript to {filepath}")


def save_text_to_file(text: str, output_file: str):
    """Save text content to a file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    logger.info(f"Content saved to {output_file}")


def get_user_input():
    """Get user input for YouTube URL and timestamps."""
    print(USER_PROMPTS["input_instructions"])
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)
    return '\n'.join(lines)


def get_context_settings():
    """Get context window settings from user."""
    try:
        context_after = int(input(USER_PROMPTS["context_after"]).strip() 
                           or str(DEFAULT_SETTINGS["default_context_after_seconds"]))
        context_before = int(input(USER_PROMPTS["context_before"]).strip() 
                            or str(DEFAULT_SETTINGS["default_context_before_seconds"]))
        return context_after, context_before
    except Exception:
        print(f"[ERROR] {ERROR_MESSAGES['invalid_context']}")
        raise ValueError(ERROR_MESSAGES["invalid_context"])


def download_and_prepare_audio(youtube_url):
    """Download audio and get metadata."""
    try:
        download_result = download_audio(youtube_url)
    except Exception as e:
        error_msg = ERROR_MESSAGES["download_failed"].format(e)
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg)
        return None
    
    if not download_result:
        print(f"[ERROR] {ERROR_MESSAGES['download_failed'].format('Unknown error')}")
        logger.error("Failed to download audio. Halting process.")
        return None
    
    return download_result


def get_or_create_transcript(audio_file_path, video_title):
    """Get existing transcript or create new one."""
    transcript_filename = f"{sanitize_filename(video_title)}_transcript.txt"
    
    try:
        if os.path.exists(transcript_filename):
            success_msg = SUCCESS_MESSAGES["transcript_exists"].format(transcript_filename)
            logger.info(success_msg)
            with open(transcript_filename, 'r', encoding='utf-8') as f:
                full_transcript = f.read()
        else:
            logger.info(f"No existing transcript found. Starting new transcription for: {video_title}")
            full_transcript = transcribe_audio_with_chunking(audio_file_path, transcript_filename)
    except Exception as e:
        error_msg = ERROR_MESSAGES["transcript_failed"].format(e)
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg)
        return None, None
    
    if not full_transcript or not full_transcript.strip():
        print(f"[ERROR] {ERROR_MESSAGES['empty_transcript']}")
        logger.error("Transcript is empty. Halting process.")
        return None, None
    
    return full_transcript, transcript_filename


def find_transcript_max_timestamp(full_transcript):
    """Find the maximum timestamp in the transcript."""
    transcript_lines = full_transcript.strip().split('\n')
    last_ts_seconds = 0
    for line in reversed(transcript_lines):
        match = re.search(r'^\[(\d{1,2}:\d{2}(?::\d{2})?)\]', line)
        if match:
            last_ts_seconds = parse_timestamp_to_seconds(match.group(1))
            break
    return last_ts_seconds


def process_timestamps(timestamps_to_process, full_transcript, context_after, context_before, video_description):
    """Process all timestamps and extract quotes."""
    extracted_quotes = []
    last_ts_seconds = find_transcript_max_timestamp(full_transcript)
    
    for i, ts_info in enumerate(timestamps_to_process):
        ts_seconds = parse_timestamp_to_seconds(ts_info.timestamp)
        
        # Check if timestamp is beyond transcript end
        if ts_seconds > last_ts_seconds:
            error_msg = ERROR_MESSAGES["timestamp_beyond_end"].format(
                ts_info.timestamp, last_ts_seconds//60, last_ts_seconds%60
            )
            logger.error(error_msg)
            print(f"[ERROR] {error_msg}")
            continue
        
        logger.info(f"Processing timestamp {i+1}/{len(timestamps_to_process)}: {ts_info.timestamp}...")
        
        try:
            segment = get_transcript_segment(
                raw_transcript=full_transcript,
                current_timestamp_index=i,
                all_timestamps=timestamps_to_process,
                manual_context_limit_sec=context_after,
                context_before_sec=context_before
            )
        except Exception as e:
            error_msg = ERROR_MESSAGES["segment_failed"].format(ts_info.timestamp, e)
            print(f"[ERROR] {error_msg}")
            logger.error(error_msg)
            continue
        
        if not segment:
            logger.warning(f"Skipping quote extraction for {ts_info.timestamp} due to empty segment.")
            print(f"[WARNING] No transcript segment found for {ts_info.timestamp}. Skipping.")
            continue
        
        try:
            quote = extract_quote_with_gemini(
                segment,
                ts_info.timestamp,
                video_description,
                ts_info.description
            )
        except Exception as e:
            error_msg = ERROR_MESSAGES["quote_failed"].format(ts_info.timestamp, e)
            print(f"[ERROR] {error_msg}")
            logger.error(error_msg)
            continue
        
        extracted_quotes.append(quote)
    
    return extracted_quotes


def save_quotes(extracted_quotes, video_title):
    """Save extracted quotes to file."""
    if extracted_quotes:
        quotes_filename = f"{sanitize_filename(video_title)}_quotes.txt"
        try:
            with open(quotes_filename, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(extracted_quotes))
        except Exception as e:
            error_msg = ERROR_MESSAGES["save_failed"].format(e)
            print(f"[ERROR] {error_msg}")
            logger.error(error_msg)
            return False
        
        success_msg = SUCCESS_MESSAGES["quotes_saved"].format(quotes_filename)
        logger.info(success_msg)
        print(success_msg)
        return True
    else:
        logger.warning("No quotes were extracted for any of the provided timestamps.")
        print("[WARNING] No quotes were extracted for any of the provided timestamps.")
        return False


def main():
    try:
        # Get user input
        input_text = get_user_input()
        youtube_url, timestamps_to_process = parse_input(input_text)
        
        # Validate input
        if not validate_input(youtube_url, timestamps_to_process):
            return
        
        # Get context settings
        context_after, context_before = get_context_settings()
        
        # Download audio and get metadata
        download_result = download_and_prepare_audio(youtube_url)
        if not download_result:
            return
        
        audio_file_path, video_title, video_description = download_result
        
        # Get or create transcript
        full_transcript, transcript_filename = get_or_create_transcript(audio_file_path, video_title)
        if not full_transcript:
            return
        
        # Process timestamps and extract quotes
        extracted_quotes = process_timestamps(
            timestamps_to_process, full_transcript, context_after, 
            context_before, video_description
        )
        
        # Save quotes
        save_quotes(extracted_quotes, video_title)
        
    except ValueError as ve:
        print(f"[ERROR] {ve}")
        logger.error(f"ValueError: {ve}")
    except FileNotFoundError as fnfe:
        print(f"[ERROR] {fnfe}")
        logger.error(f"FileNotFoundError: {fnfe}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        logger.error(f"An unexpected error occurred in the main execution block: {e}")


if __name__ == "__main__":
    main()
