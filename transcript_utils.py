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
        logger.info(
            f"Last timestamp. Using manual context limit of "
            f"{context_after_sec}s."
        )
    else:
        next_ts_info = all_timestamps[current_timestamp_index + 1]
        next_timestamp_seconds = parse_timestamp_to_seconds(
            next_ts_info.timestamp
        )
        duration_to_next_ts = next_timestamp_seconds - target_seconds
        context_after_sec = min(duration_to_next_ts, manual_context_limit_sec)
        logger.info(
            f"Next timestamp is at {next_ts_info.timestamp} "
            f"({duration_to_next_ts}s away). Using context of "
            f"{context_after_sec}s."
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
            f"Could not find transcript segment for timestamp "
            f"{current_ts_info.timestamp}."
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
    
    # Configure Gemini with timeout
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
    
    # Log audio file info for debugging
    logger.info(f"Audio file size for transcription: {len(audio_data)} bytes")
    
    try:
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        logger.info(f"Base64 encoded size: {len(audio_base64)} characters")
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
    logger.info(f"Using model: {DEFAULT_SETTINGS['gemini_model']}")
    logger.info(f"Prompt length: {len(TRANSCRIPTION_PROMPT)} characters")
    
    try:
        # Add request configuration with increased token limit
        response = model.generate_content(
            content_parts,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                max_output_tokens=DEFAULT_SETTINGS["max_output_tokens"],
            )
        )
        logger.info("Received response from Gemini API")
        
        # Debug response object
        logger.info(f"Response object type: {type(response)}")
        logger.info(f"Response has text attribute: {hasattr(response, 'text')}")
        
        if hasattr(response, 'candidates') and response.candidates:
            logger.info(f"Number of candidates: {len(response.candidates)}")
            for i, candidate in enumerate(response.candidates):
                logger.info(f"Candidate {i} finish_reason: {getattr(candidate, 'finish_reason', 'unknown')}")
        
    except Exception as e:
        error_msg = f"Failed to get response from Gemini API: {e}"
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg)
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise
    
    # Enhanced response validation
    if not response:
        error_msg = "Gemini API returned None response"
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check finish reason first to provide better error messages
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        finish_reason = getattr(candidate, 'finish_reason', None)
        
        if finish_reason == 2:  # MAX_TOKENS - response was truncated
            logger.warning("Response was truncated due to token limit")
            # Try to extract partial content if available
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    partial_text = ""
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            partial_text += part.text
                    
                    if partial_text.strip():
                        logger.info(f"Extracted partial transcript: {len(partial_text)} characters")
                        transcript_text = partial_text.strip()
                        
                        # Save partial transcript with warning
                        try:
                            with open(transcript_filename, 'w', encoding='utf-8') as f:
                                f.write(f"# WARNING: This transcript was truncated due to length limits\n")
                                f.write(f"# Partial transcript ({len(transcript_text)} characters)\n\n")
                                f.write(transcript_text)
                            logger.info(f"Partial transcript saved to {transcript_filename}")
                        except Exception as e:
                            print(f"[ERROR] Failed to save partial transcript: {e}")
                            raise
                        
                        return transcript_text
            
            # If we can't extract partial content, raise error
            error_msg = "Response truncated due to token limit and no partial content available"
            print(f"[ERROR] {error_msg}")
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        elif finish_reason == 3:  # SAFETY
            error_msg = "Response blocked by safety filters"
            print(f"[ERROR] {error_msg}")
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        elif finish_reason == 4:  # RECITATION
            error_msg = "Response blocked due to recitation concerns"
            print(f"[ERROR] {error_msg}")
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    # Original text validation
    if not hasattr(response, 'text'):
        error_msg = "Gemini API response missing text attribute"
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not response.text:
        error_msg = "Empty response from Gemini API"
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg)
        
        # Log additional debugging info
        if hasattr(response, 'candidates') and response.candidates:
            for i, candidate in enumerate(response.candidates):
                finish_reason = getattr(candidate, 'finish_reason', 'unknown')
                logger.error(f"Candidate {i} finish_reason: {finish_reason}")
                if hasattr(candidate, 'safety_ratings'):
                    logger.error(f"Candidate {i} safety_ratings: {candidate.safety_ratings}")
        
        raise ValueError(ERROR_MESSAGES["gemini_response_empty"])
    
    # Log successful response info
    transcript_text = response.text.strip()
    logger.info("Successfully received transcript from Gemini API.")
    logger.info(f"Transcript length: {len(transcript_text)} characters")
    logger.info(f"Transcript preview: {transcript_text[:200]}...")
    
    try:
        with open(transcript_filename, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        logger.info(f"Transcript saved to {transcript_filename}")
    except Exception as e:
        print(f"[ERROR] Failed to save transcript to file: {e}")
        raise
    
    return transcript_text


@retry(stop=stop_after_attempt(DEFAULT_SETTINGS["retry_attempts"]), 
       wait=wait_exponential(multiplier=1, min=4, max=10))
def transcribe_audio_with_dynamic_chunking(audio_path: str, transcript_filename: str) -> str:
    """
    Transcribe audio with automatic chunking when hitting token limits.
    Will recursively split chunks smaller if token limits are exceeded.
    """
    logger.info(f"Attempting transcription with dynamic chunking: {audio_path}")
    
    try:
        # Try direct transcription first
        transcript = transcribe_audio(audio_path, transcript_filename)
        
        # Check if we got a complete transcript (no truncation warnings)
        if "WARNING: This transcript was truncated" in transcript:
            logger.warning("Token limit exceeded, attempting to split into smaller chunks")
            return transcribe_with_progressive_chunking(audio_path, transcript_filename)
        
        logger.info(f"Successfully transcribed without chunking: {len(transcript)} characters")
        return transcript
        
    except ValueError as e:
        if "token limit" in str(e).lower() or "truncated" in str(e).lower():
            logger.warning("Token limit exceeded on initial attempt, splitting into chunks")
            return transcribe_with_progressive_chunking(audio_path, transcript_filename)
        else:
            # Re-raise non-token-limit errors
            raise


def transcribe_with_progressive_chunking(audio_path: str, transcript_filename: str, 
                                       chunk_size_min: float = None) -> str:
    """
    Progressively split audio into smaller chunks until transcription succeeds.
    """
    from audio_utils import split_audio_chunks, get_audio_file_info
    
    if chunk_size_min is None:
        # Start with configured chunk size
        chunk_size_min = DEFAULT_SETTINGS["chunk_length_minutes"]
    
    # Get file duration to check minimum viable chunk size
    file_size_MB, duration_min = get_audio_file_info(audio_path)
    
    # Don't go below 2-minute chunks (or file duration if shorter)
    min_chunk_size = min(2.0, duration_min / 4)  # At most 4 chunks for very short files
    
    logger.info(f"Attempting progressive chunking with {chunk_size_min:.1f}min chunks")
    
    if chunk_size_min < min_chunk_size:
        logger.error(f"Cannot split further: chunk size {chunk_size_min:.1f}min below minimum {min_chunk_size:.1f}min")
        # Try transcription anyway and return partial result
        try:
            partial_transcript = transcribe_audio(audio_path, transcript_filename)
            logger.warning("Returning partial transcript - cannot split audio further")
            return partial_transcript
        except Exception as e:
            logger.error(f"Even partial transcription failed: {e}")
            raise ValueError("Audio too dense for available token limits")
    
    # Split into chunks using the existing function
    chunks = split_audio_chunks(audio_path, chunk_length_min=chunk_size_min, overlap_sec=15)
    
    if len(chunks) <= 1:
        # Cannot split further with current parameters
        logger.warning("Cannot create multiple chunks, attempting single chunk transcription")
        try:
            return transcribe_audio(audio_path, transcript_filename)
        except:
            raise ValueError("Cannot split audio into smaller chunks")
    
    logger.info(f"Split into {len(chunks)} chunks of ~{chunk_size_min:.1f} minutes each")
    
    # Process each chunk with potential recursive splitting
    transcripts = []
    failed_chunks = []
    
    for idx, (chunk_path, start_sec) in enumerate(chunks):
        chunk_transcript_file = transcript_filename.replace('.txt', f'_progchunk{idx+1}.txt')
        logger.info(f"Processing progressive chunk {idx+1}/{len(chunks)}: offset {start_sec}s")
        
        try:
            # Try to transcribe this chunk
            chunk_transcript = transcribe_audio(chunk_path, chunk_transcript_file)
            
            # Check if this chunk was also truncated
            if "WARNING: This transcript was truncated" in chunk_transcript:
                logger.warning(f"Chunk {idx+1} was truncated, trying smaller chunks")
                # Recursively split this chunk further
                sub_transcript = transcribe_with_progressive_chunking(
                    chunk_path, chunk_transcript_file, chunk_size_min / 2
                )
                chunk_transcript = sub_transcript
            
            if chunk_transcript and chunk_transcript.strip():
                # Adjust timestamps for this chunk's offset
                adjusted_transcript = adjust_transcript_timestamps(chunk_transcript, start_sec)
                transcripts.append(adjusted_transcript)
                logger.info(f"Successfully processed chunk {idx+1}: {len(chunk_transcript)} chars")
            else:
                logger.warning(f"Empty transcript from chunk {idx+1}")
                failed_chunks.append(idx+1)
                
        except Exception as e:
            logger.error(f"Failed to process chunk {idx+1}: {e}")
            failed_chunks.append(idx+1)
            continue
    
    if not transcripts:
        raise ValueError("All progressive chunks failed to transcribe")
    
    if failed_chunks:
        logger.warning(f"Failed to process chunks: {failed_chunks}")
    
    logger.info(f"Successfully processed {len(transcripts)}/{len(chunks)} chunks")
    
    # Combine transcripts with deduplication
    return combine_transcripts_with_deduplication(transcripts, transcript_filename)


def combine_transcripts_with_deduplication(transcripts: list, output_filename: str) -> str:
    """
    Combine multiple transcript chunks with intelligent deduplication.
    """
    if not transcripts:
        return ""
    
    if len(transcripts) == 1:
        result = transcripts[0]
    else:
        # Combine with overlap deduplication
        combined_lines = []
        seen_content = set()
        
        for transcript in transcripts:
            lines = transcript.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Skip warning headers
                if line.startswith('#'):
                    continue
                
                # Extract content without timestamp for deduplication
                if ']' in line and line.startswith('['):
                    content = line.split(']', 1)[1].strip()
                else:
                    content = line
                
                # Use first 30 characters of content as deduplication key
                content_key = content[:30] if len(content) > 30 else content
                
                if content_key not in seen_content:
                    combined_lines.append(line)
                    seen_content.add(content_key)
                else:
                    logger.debug(f"Skipping duplicate: {content_key}...")
        
        result = '\n'.join(combined_lines)
    
    # Save combined result
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(result)
        logger.info(f"Combined transcript saved to {output_filename}")
        logger.info(f"Final transcript length: {len(result)} characters")
    except Exception as e:
        logger.error(f"Failed to save combined transcript: {e}")
    
    return result


@retry(stop=stop_after_attempt(DEFAULT_SETTINGS["retry_attempts"]), 
       wait=wait_exponential(multiplier=1, min=4, max=10))
def transcribe_audio_with_chunking(audio_path: str, transcript_filename: str) -> str:
    """
    Main transcription function with intelligent chunking and dynamic splitting.
    """
    file_size_MB, duration_min = get_audio_file_info(audio_path)
    logger.info(f"Audio file size: {file_size_MB:.2f} MB, duration: {duration_min:.2f} min")
    
    max_duration = DEFAULT_SETTINGS["max_duration_minutes"]
    max_size = DEFAULT_SETTINGS["max_file_size_mb"]
    
    # Check if chunking is needed based on size/duration thresholds
    if duration_min <= max_duration and file_size_MB <= max_size:
        logger.info("File within limits, attempting transcription with dynamic chunking")
        return transcribe_audio_with_dynamic_chunking(audio_path, transcript_filename)
    
    # File is large, use progressive chunking approach
    logger.info(f"File exceeds limits (>{max_duration}min or >{max_size}MB)")
    logger.info("Using progressive chunking approach")
    
    return transcribe_with_progressive_chunking(audio_path, transcript_filename)