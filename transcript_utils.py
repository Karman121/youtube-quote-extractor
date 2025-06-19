import re
import os
import base64
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
# from pydub.utils import mediainfo  # Removed unused import
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from audio_utils import get_audio_file_info
from utils import sanitize_filename, format_timestamp
from config import (
    DEFAULT_SETTINGS, 
    TRANSCRIPTION_PROMPT, 
    ERROR_MESSAGES, 
    SUCCESS_MESSAGES
)


logger = logging.getLogger(__name__)


@dataclass
class TimestampInfo:
    timestamp: str
    description: str = ""


def parse_input(text_block: str) -> Tuple[Optional[str], List[TimestampInfo]]:
    """
    Parses a block of unstructured text to extract a URL and a list of
    timestamped descriptions. Handles cases where descriptions are missing.
    """
    youtube_url = None
    timestamps_data = []
    url_pattern = re.compile(r'https?://[^\s]+')
    timestamp_pattern = re.compile(r'^(\d{1,2}:\d{2})(?:\s*-\s*(.*))?')
    lines = text_block.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        url_match = url_pattern.search(line)
        if url_match and not youtube_url:
            youtube_url = url_match.group(0)
            continue
        timestamp_match = timestamp_pattern.match(line)
        if timestamp_match:
            timestamp = timestamp_match.group(1).strip()
            description_match = timestamp_match.group(2)
            description = (
                description_match.strip()
                if description_match is not None else ""
            )
            timestamps_data.append(TimestampInfo(
                timestamp=timestamp,
                description=description
            ))
    return youtube_url, timestamps_data


def parse_timestamp_to_seconds(timestamp: str) -> int:
    parts = list(map(int, timestamp.split(':')))
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return 0


def extract_timestamps_and_descriptions(text: str) -> List[TimestampInfo]:
    timestamp_patterns = [
        r'(\d{1,2}:\d{2}(?::\d{2})?)',
        r'(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]?\s*(.*?)(?=\n\d{1,2}:\d{2}|$)',
        r'(\d{1,2}:\d{2}(?::\d{2})?)\s+(.*?)(?=\n\d{1,2}:\d{2}|$)',
        r'@?(\d{1,2}:\d{2}(?::\d{2})?)',
    ]
    results = []
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                timestamp = match.group(1)
                description = (
                    match.group(2).strip() if len(match.groups()) > 1 else None
                )
                if description:
                    results.append(TimestampInfo(
                        timestamp=timestamp,
                        description=description
                    ))
                else:
                    results.append(TimestampInfo(timestamp=timestamp))
                break
    logger.info("=== Extracted Timestamps ===")
    for info in results:
        logger.info(f"Timestamp: {info.timestamp}")
        if info.description:
            logger.info(f"Description: {info.description}")
    return results


def get_transcript_segment(
    raw_transcript: str,
    current_timestamp_index: int,
    all_timestamps: List[TimestampInfo],
    manual_context_limit_sec: int,
    context_before_sec: int = 30
) -> str:
    current_ts_info = all_timestamps[current_timestamp_index]
    target_seconds = parse_timestamp_to_seconds(current_ts_info.timestamp)
    is_last_timestamp = (current_timestamp_index == len(all_timestamps) - 1)
    if is_last_timestamp:
        context_after_sec = manual_context_limit_sec
        logger.info(f"Last timestamp. Using manual context limit of {context_after_sec}s.")
    else:
        next_ts_info = all_timestamps[current_timestamp_index + 1]
        next_timestamp_seconds = parse_timestamp_to_seconds(next_ts_info.timestamp)
        duration_to_next_ts = next_timestamp_seconds - target_seconds
        context_after_sec = min(duration_to_next_ts, manual_context_limit_sec)
        logger.info(
            f"Next timestamp is at {next_ts_info.timestamp} "
            f"({duration_to_next_ts}s away). Using context of {context_after_sec}s."
        )
    start_time = max(0, target_seconds - context_before_sec)
    end_time = target_seconds + context_after_sec
    segment_lines = []
    for line in raw_transcript.strip().split('\n'):
        match = re.search(r'^\[(\d{1,2}:\d{2}(?::\d{2})?)\]', line)
        if match:
            line_ts = match.group(1)
            current_seconds = parse_timestamp_to_seconds(line_ts)
            if start_time <= current_seconds <= end_time:
                segment_lines.append(line)
    segment = '\n'.join(segment_lines)
    if not segment:
        logger.warning(
            f"Could not find transcript segment for timestamp {current_ts_info.timestamp}."
        )
    return segment


def adjust_transcript_timestamps(transcript: str, offset_sec: int) -> str:
    def repl(match):
        ts = match.group(1)
        parts = list(map(int, ts.split(':')))
        if len(parts) == 3:
            total_sec = parts[0]*3600 + parts[1]*60 + parts[2] + offset_sec
        else:
            total_sec = parts[0]*60 + parts[1] + offset_sec
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        if h > 0:
            return f"[{h:02d}:{m:02d}:{s:02d}]"
        else:
            return f"[{m:02d}:{s:02d}]"
    return re.sub(r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]', repl, transcript)


def save_transcript_to_file(transcript: str, filename: str):
    filepath = os.path.join(".", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(transcript)
    logger.info(f"Saved transcript to {filepath}")


# Transcription functions
load_dotenv()


@retry(stop=stop_after_attempt(DEFAULT_SETTINGS["retry_attempts"]), 
       wait=wait_exponential(multiplier=1, min=4, max=10))
def transcribe_audio(audio_path: str, transcript_filename: str) -> str:
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print(f"[ERROR] {ERROR_MESSAGES['gemini_api_key_missing']}")
        raise ValueError(ERROR_MESSAGES["gemini_api_key_missing"])
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(DEFAULT_SETTINGS["gemini_model"])
    if not os.path.exists(audio_path):
        print(f"[ERROR] {ERROR_MESSAGES['audio_file_not_found'].format(audio_path)}")
        raise FileNotFoundError(ERROR_MESSAGES["audio_file_not_found"].format(audio_path))
    try:
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()
    except Exception as e:
        print(f"[ERROR] Failed to read audio file: {e}")
        raise
    if not audio_data:
        print(f"[ERROR] {ERROR_MESSAGES['audio_file_empty']}")
        raise ValueError(ERROR_MESSAGES["audio_file_empty"])
    try:
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    except Exception as e:
        print(f"[ERROR] Failed to encode audio file: {e}")
        raise
    
    content_parts = [
        {"text": TRANSCRIPTION_PROMPT},
        {
            "inline_data": {
                "mime_type": "audio/mpeg",
                "data": audio_base64
            }
        }
    ]
    logger.info("Sending transcription request to Gemini API...")
    try:
        response = model.generate_content(content_parts)
    except Exception as e:
        print(f"[ERROR] {ERROR_MESSAGES['gemini_api_failed'].format(e)}")
        raise
    if not response or not response.text:
        print(f"[ERROR] {ERROR_MESSAGES['gemini_response_empty']}")
        raise ValueError(ERROR_MESSAGES["gemini_response_empty"])
    logger.info("Successfully received transcript from Gemini API.")
    try:
        with open(transcript_filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
    except Exception as e:
        print(f"[ERROR] Failed to save transcript to file: {e}")
        raise
    logger.info(f"Transcript saved to {transcript_filename}")
    return response.text


@retry(stop=stop_after_attempt(DEFAULT_SETTINGS["retry_attempts"]), 
       wait=wait_exponential(multiplier=1, min=4, max=10))
def transcribe_audio_with_chunking(audio_path: str, transcript_filename: str) -> str:
    file_size_MB, duration_min = get_audio_file_info(audio_path)
    logger.info(f"Audio file size: {file_size_MB:.2f} MB, duration: {duration_min:.2f} min")
    chunking = False
    chunks = []
    
    max_duration = DEFAULT_SETTINGS["max_duration_minutes"]
    max_size = DEFAULT_SETTINGS["max_file_size_mb"]
    chunk_length = DEFAULT_SETTINGS["chunk_length_minutes"]
    overlap = DEFAULT_SETTINGS["overlap_seconds"]
    
    if duration_min > max_duration or file_size_MB > max_size:
        logger.info(SUCCESS_MESSAGES["chunking_needed"].format(
            max_duration, max_size, chunk_length, overlap))
        from audio_utils import split_audio_chunks
        chunks = split_audio_chunks(audio_path, chunk_length_min=chunk_length, overlap_sec=overlap)
        chunking = True
    else:
        logger.info(SUCCESS_MESSAGES["no_chunking"])
    
    if not chunking:
        return transcribe_audio(audio_path, transcript_filename)
    
    transcripts = []
    for idx, (chunk_path, start_sec) in enumerate(chunks):
        chunk_transcript_file = transcript_filename.replace('.txt', f'_chunk{idx+1}.txt')
        logger.info(f"Transcribing chunk {idx+1}/{len(chunks)}: {chunk_path} (offset {start_sec}s)")
        chunk_transcript = transcribe_audio(chunk_path, chunk_transcript_file)
        chunk_transcript = adjust_transcript_timestamps(chunk_transcript, start_sec)
        transcripts.append(chunk_transcript)
    
    stitched = []
    prev_lines = set()
    for t in transcripts:
        lines = t.strip().split('\n')
        new_lines = [line for line in lines if line not in prev_lines]
        stitched.extend(new_lines)
        prev_lines.update(new_lines)
    
    full_transcript = '\n'.join(stitched)
    with open(transcript_filename, 'w', encoding='utf-8') as f:
        f.write(full_transcript)
    logger.info(f"Stitched transcript saved to {transcript_filename}")
    return full_transcript