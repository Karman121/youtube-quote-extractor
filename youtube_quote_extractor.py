# =========================
# Imports and Configuration
# =========================
import os
import re
import base64
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
import yt_dlp
import google.generativeai as genai
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential
from pydub import AudioSegment
from pydub.utils import mediainfo

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =========================
# Data Classes
# =========================


@dataclass
class TimestampInfo:
    timestamp: str
    description: str = ""


# =========================
# Utility Functions
# =========================

def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', filename)


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


def format_timestamp(timestamp: str) -> str:
    """Convert timestamp to MM:SS format."""
    try:
        # Extract minutes and seconds from the timestamp
        match = re.match(r'\[(\d+):(\d+):(\d+)\]', timestamp)
        if match:
            hours, minutes, seconds = map(int, match.groups())
            total_seconds = hours * 3600 + minutes * 60 + seconds
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"[{minutes:02d}:{seconds:02d}]"
    except Exception as e:
        logger.error(f"Error formatting timestamp: {str(e)}")
    return timestamp


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


def extract_youtube_link(text: str) -> Optional[str]:
    # Extract YouTube link
    youtube_pattern = (
        r'@?(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)'
        r'[a-zA-Z0-9_-]+(?:\?[^&\s]*)?)'
    )
    match = re.search(youtube_pattern, text)
    return match.group(1) if match else None


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)',
        r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
        r'youtube\.com/v/([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def save_transcript_to_file(transcript: str, filename: str):
    """Save transcript to a file."""
    filepath = os.path.join(".", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(transcript)
    logger.info(f"Saved transcript to {filepath}")


def download_audio(url: str, output_path: str = ".") -> Optional[Tuple[str, str, str]]:
    """
    Downloads audio from a YouTube URL with correct caching and fallback logic.
    Returns (audio_path, title, description)
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'video')
        description = info.get('description', '')
        sanitized_title = sanitize_filename(title)
        expected_filepath = os.path.join(
            output_path, f"{sanitized_title}.mp3"
        )
        if os.path.exists(expected_filepath):
            logger.info(
                f"✅ Audio file already exists: '{expected_filepath}'. "
                "Skipping download."
            )
            return expected_filepath, title, description
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_path, f"{sanitized_title}.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        logger.info(f"Downloading audio: {url}")
        ydl.download([url])
        logger.info(f"Audio downloaded: {expected_filepath}")
        return expected_filepath, title, description


def split_audio(audio_path, chunk_duration):
    """Split audio file into chunks of specified duration."""
    audio = AudioSegment.from_mp3(audio_path)
    duration_ms = len(audio)
    chunk_duration_ms = chunk_duration * 1000
    
    # Calculate number of chunks needed, ensuring we cover the entire duration
    num_chunks = max(
        1, (duration_ms + chunk_duration_ms - 1) // chunk_duration_ms
    )
    logger.info(
        f"Audio duration: {duration_ms/1000:.2f}s, splitting into {num_chunks} chunks"
    )
    
    chunks = []
    for i in range(num_chunks):
        start_ms = i * chunk_duration_ms
        end_ms = min((i + 1) * chunk_duration_ms, duration_ms)
        
        # Add 10 second overlap between chunks to avoid cutting words
        if i > 0:
            start_ms = max(0, start_ms - 10000)  # 10 seconds overlap, but don't go below 0
        if i < num_chunks - 1:
            # 10 seconds overlap, but don't exceed duration
            end_ms = min(
                duration_ms, end_ms + 10000
            )
            
        chunk = audio[start_ms:end_ms]
        chunk_path = f"{audio_path}_chunk_{i+1}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunks.append(chunk_path)
        logger.info(
            f"Created chunk {i+1}/{num_chunks}: "
            f"{start_ms/1000:.2f}s - {end_ms/1000:.2f}s"
        )

    return chunks


@sleep_and_retry
@limits(calls=1.8, period=1)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def upload_to_gemini_with_retry(path, mime_type=None):
    """Upload file to Gemini with retry logic."""
    try:
        logger.debug(f"Starting upload for: {os.path.basename(path)}")
        genai.configure(
            api_key=os.getenv("GEMINI_API_KEY"),
            transport="rest"
        )
        file = genai.upload_file(path, mime_type=mime_type)
        logger.debug(f"Upload complete: {os.path.basename(path)}")
        return file
    except Exception as e:
        logger.error(f"Upload failed for {os.path.basename(path)}: {str(e)}")
        raise


@sleep_and_retry
@limits(calls=1.8, period=1)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def process_file_with_retry(chat_session, file):
    """Process file with Gemini with retry logic."""
    try:
        logger.debug(f"Processing: {file.display_name}")
        response = chat_session.send_message(
            "You are a professional audio transcriptionist. Your task is to:\n"
            "1. Transcribe the audio with high accuracy\n"
            "2. Identify and label each speaker by their name (e.g., 'Bye Manning', "
            "'Brian Lewis')\n"
            "3. Format each line as: '[MM:SS] Speaker Name: Text'\n"
            "4. Include timestamps in MM:SS format, starting from the exact time provided\n"
            "5. Keep complete sentences and thoughts together\n"
            "6. Preserve the natural flow of conversation\n"
            "7. If you can't identify a speaker, use 'Speaker 1', 'Speaker 2', etc.\n"
            "8. Add a new line between different speakers\n"
            "9. If it's a single speaker, break it into paragraphs.\n"
            (
                "10. IMPORTANT: Maintain exact timestamps as provided in the audio - "
                "do not adjust or estimate them."
            )
        )
        return response
    except Exception as e:
        logger.error(f"Processing failed for {file.display_name}: {str(e)}")
        raise


def parse_vtt_timestamp(timestamp: str) -> float:
    """Convert VTT timestamp to seconds.
    Handles both MM:SS and HH:MM:SS formats.
    """
    parts = timestamp.split(':')
    if len(parts) == 2:  # MM:SS format
        minutes, seconds = parts
        return float(minutes) * 60 + float(seconds)
    elif len(parts) == 3:  # HH:MM:SS format
        hours, minutes, seconds = parts
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp}")


def get_transcript_segment(
    raw_transcript: str,
    current_timestamp_index: int,
    all_timestamps: List[TimestampInfo],
    manual_context_limit_sec: int,
    context_before_sec: int = 30
) -> str:
    """
    Extracts a transcript segment with a dynamically calculated context window.
    Args:
        raw_transcript: The full transcript text.
        current_timestamp_index: The index (position) of the current timestamp being processed.
        all_timestamps: The complete list of all TimestampInfo objects.
        manual_context_limit_sec: The user-defined maximum number of seconds for context.
        context_before_sec: How many seconds of context to include *before* the timestamp.
    """
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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def extract_quote_with_gemini(
    transcript_segment: str,
    timestamp: str,
    video_description: Optional[str],
    user_description: Optional[str]
) -> str:
    """
    Extracts a newsworthy quote from a transcript segment using Gemini.
    """
    api_key = os.getenv('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    focus_instruction = (
        f"The user is particularly interested in quotes related to: '{user_description}'"
        if user_description else ""
    )
    prompt = (
        f"""
    You are a professional journalist extracting meaningful quotes for a news article. Your task is to:
    1. Analyze the transcript, video description, and any context provided.
    2. Extract insightful, newsworthy quotes suitable for article use.
    3. **Crucial Task**: The user will provide a timestamp. Treat this timestamp as an **anchor point**. Your main goal is to find the complete conversational exchange (e.g., the full question and its full answer) that this anchor point falls within. You must read backwards from the anchor to find the beginning of the exchange.
    4. Speaker identification:
       - Use names, roles, or the video description to confidently assign real names (e.g., "Scott Agnes", "Tyrese Haliburton") instead of generic labels.
       - If unsure after checking context, use "Unknown Speaker".
       - Be consistent with names across all quotes.
    5. In Q&A settings:
       - Extract both the full question and the full answer as separate quotes, as they form a complete exchange.
    6. Quotes must be complete thoughts. If a statement starts or ends with a conjunction (e.g., 'and', 'but'), include the adjacent sentence(s) from the same speaker to make it a complete thought.
    7. Combine uninterrupted statements from a single speaker into one quote.
    8. Prioritize quotes that reveal new insights, strong opinions, or emotional stakes.
    9. DO NOT include filler words, small talk, or incomplete fragments.
    10. Format each quote as: `Speaker Name: "The full quote."`
    11. Output ONLY the formatted quotes. Do not add any introductory text, summaries, or explanations.
    12. If a user description is provided, that is your primary focus for selecting what is "newsworthy."

    **Context provided by the user (this is the most important input, if provided by user):**
    {focus_instruction if focus_instruction else "No specific topic was provided. Use your judgment to find the most newsworthy quote."}

    **Video Description (for overall context):**
    {video_description if video_description else 'No description available.'}

    **Transcript Segment (The user's point of interest is at or around timestamp {timestamp}):**
    ---
    {transcript_segment}
    ---
    """
    )
    logger.info(f"Extracting quote for timestamp {timestamp}...")
    response = model.generate_content(prompt)
    return f"[{timestamp}]\n{response.text.strip()}"


def save_text_to_file(text: str, output_file: str):
    """Save text content to a file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    logger.info(f"Content saved to {output_file}")


def main():
    try:
        print("Paste your YouTube URL and timestamps (MM:SS - description) below. End input with an empty line:")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line.strip():
                break
            lines.append(line)
        input_text = '\n'.join(lines)
        youtube_url, timestamps_to_process = parse_input(input_text)
        if not youtube_url:
            print("[ERROR] No YouTube URL found in your input. Please provide a valid URL.")
            logger.error("No YouTube URL found in input.")
            return
        if not timestamps_to_process:
            print("[ERROR] No timestamps found in your input. Please provide at least one timestamp in MM:SS or HH:MM:SS format.")
            logger.error("No timestamps found in input.")
            return
        # Validate timestamp formats
        for ts_info in timestamps_to_process:
            if not re.match(r'^(\d{1,2}:\d{2})(?::\d{2})?$', ts_info.timestamp):
                print(f"[ERROR] Invalid timestamp format: {ts_info.timestamp}. Use MM:SS or HH:MM:SS.")
                logger.error(f"Invalid timestamp format: {ts_info.timestamp}")
                return
        try:
            manual_context_limit_sec = int(input("Enter context window after timestamp (seconds, e.g. 90): ").strip() or "90")
            context_before_sec = int(input("Enter context window before timestamp (seconds, e.g. 30): ").strip() or "30")
        except Exception:
            print("[ERROR] Invalid input for context window. Please enter a number.")
            return
        # Download audio and get metadata
        try:
            download_result = download_audio(youtube_url)
        except Exception as e:
            print(f"[ERROR] Failed to download audio: {e}")
            logger.error(f"Failed to download audio: {e}")
            return
        if not download_result:
            print("[ERROR] Failed to download audio. Halting process.")
            logger.error("Failed to download audio. Halting process.")
            return
        audio_file_path, video_title, video_description = download_result
        transcript_filename = f"{sanitize_filename(video_title)}_transcript.txt"
        try:
            if os.path.exists(transcript_filename):
                logger.info(f"✅ Found existing transcript file: {transcript_filename}. Skipping transcription.")
                with open(transcript_filename, 'r', encoding='utf-8') as f:
                    full_transcript = f.read()
            else:
                logger.info(f"No existing transcript found. Starting new transcription for: {video_title}")
                full_transcript = transcribe_audio_with_chunking(audio_file_path, transcript_filename)
        except Exception as e:
            print(f"[ERROR] Failed to read or write transcript file: {e}")
            logger.error(f"Failed to read or write transcript file: {e}")
            return
        if not full_transcript or not full_transcript.strip():
            print("[ERROR] Transcript is empty. Halting process.")
            logger.error("Transcript is empty. Halting process.")
            return
        extracted_quotes = []
        # Find the maximum timestamp in the transcript (in seconds)
        transcript_lines = full_transcript.strip().split('\n')
        last_ts_seconds = 0
        for line in reversed(transcript_lines):
            match = re.search(r'^\[(\d{1,2}:\d{2}(?::\d{2})?)\]', line)
            if match:
                last_ts_seconds = parse_timestamp_to_seconds(match.group(1))
                break
        for i, ts_info in enumerate(timestamps_to_process):
            ts_seconds = parse_timestamp_to_seconds(ts_info.timestamp)
            if ts_seconds > last_ts_seconds:
                logger.error(f"Timestamp {ts_info.timestamp} is beyond the end of the transcript/audio (max is {last_ts_seconds//60}:{last_ts_seconds%60:02d}). Skipping.")
                print(f"[ERROR] Timestamp {ts_info.timestamp} is beyond the end of the transcript/audio (max is {last_ts_seconds//60}:{last_ts_seconds%60:02d}). Skipping.")
                continue
            logger.info(f"Processing timestamp {i+1}/{len(timestamps_to_process)}: {ts_info.timestamp}...")
            try:
                segment = get_transcript_segment(
                    raw_transcript=full_transcript,
                    current_timestamp_index=i,
                    all_timestamps=timestamps_to_process,
                    manual_context_limit_sec=manual_context_limit_sec,
                    context_before_sec=context_before_sec
                )
            except Exception as e:
                print(f"[ERROR] Failed to extract transcript segment for {ts_info.timestamp}: {e}")
                logger.error(f"Failed to extract transcript segment for {ts_info.timestamp}: {e}")
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
                print(f"[ERROR] Failed to extract quote for {ts_info.timestamp}: {e}")
                logger.error(f"Failed to extract quote for {ts_info.timestamp}: {e}")
                continue
            extracted_quotes.append(quote)
        if extracted_quotes:
            quotes_filename = f"{sanitize_filename(video_title)}_quotes.txt"
            try:
                save_text_to_file('\n\n'.join(extracted_quotes), quotes_filename)
            except Exception as e:
                print(f"[ERROR] Failed to save quotes to file: {e}")
                logger.error(f"Failed to save quotes to file: {e}")
                return
            logger.info(f"All quotes saved to {quotes_filename}")
            print(f"All quotes saved to {quotes_filename}")
        else:
            logger.warning("No quotes were extracted for any of the provided timestamps.")
            print("[WARNING] No quotes were extracted for any of the provided timestamps.")
    except ValueError as ve:
        print(f"[ERROR] {ve}")
        logger.error(f"ValueError: {ve}")
    except FileNotFoundError as fnfe:
        print(f"[ERROR] {fnfe}")
        logger.error(f"FileNotFoundError: {fnfe}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        logger.error(f"An unexpected error occurred in the main execution block: {e}")


def get_audio_file_info(audio_path: str) -> Tuple[float, float]:
    """
    Returns (file_size_MB, duration_minutes) for the given audio file.
    """
    file_size_MB = os.path.getsize(audio_path) / (1024 * 1024)
    info = mediainfo(audio_path)
    duration_sec = float(info['duration'])
    duration_minutes = duration_sec / 60
    return file_size_MB, duration_minutes


def split_audio_chunks(audio_path: str, chunk_length_min: int = 30, overlap_sec: int = 30) -> List[Tuple[str, int]]:
    """
    Splits audio into chunks of chunk_length_min (in minutes) with overlap_sec (in seconds).
    Returns a list of (chunk_path, chunk_start_sec).
    """
    audio = AudioSegment.from_mp3(audio_path)
    duration_ms = len(audio)
    chunk_length_ms = chunk_length_min * 60 * 1000
    overlap_ms = overlap_sec * 1000
    chunks = []
    start_ms = 0
    chunk_idx = 1
    while start_ms < duration_ms:
        end_ms = min(start_ms + chunk_length_ms, duration_ms)
        chunk = audio[start_ms:end_ms]
        chunk_path = f"{audio_path}_chunk_{chunk_idx}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunks.append((chunk_path, start_ms // 1000))
        if end_ms == duration_ms:
            break
        start_ms = end_ms - overlap_ms  # overlap for next chunk
        chunk_idx += 1
    return chunks


def adjust_transcript_timestamps(transcript: str, offset_sec: int) -> str:
    """
    Adjusts all [MM:SS] or [HH:MM:SS] timestamps in the transcript by offset_sec.
    """
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


def transcribe_audio_with_chunking(audio_path: str, transcript_filename: str) -> str:
    """
    Transcribe audio, chunking if needed. Returns the full transcript.
    Chunk if duration > 50 min or file size > 100 MB, each chunk <= 30 min.
    """
    file_size_MB, duration_min = get_audio_file_info(audio_path)
    logger.info(f"Audio file size: {file_size_MB:.2f} MB, duration: {duration_min:.2f} min")
    chunking = False
    chunks = []
    if duration_min > 50 or file_size_MB > 100:
        logger.info("Chunking: duration > 50min or file size > 100MB. Splitting into 30min chunks with 30s overlap.")
        chunks = split_audio_chunks(audio_path, chunk_length_min=30, overlap_sec=30)
        chunking = True
    else:
        logger.info("No chunking needed.")
    if not chunking:
        return transcribe_audio(audio_path, transcript_filename)
    # Transcribe each chunk and stitch
    transcripts = []
    for idx, (chunk_path, start_sec) in enumerate(chunks):
        chunk_transcript_file = transcript_filename.replace('.txt', f'_chunk{idx+1}.txt')
        logger.info(f"Transcribing chunk {idx+1}/{len(chunks)}: {chunk_path} (offset {start_sec}s)")
        chunk_transcript = transcribe_audio(chunk_path, chunk_transcript_file)
        # Adjust timestamps for this chunk
        chunk_transcript = adjust_transcript_timestamps(chunk_transcript, start_sec)
        transcripts.append(chunk_transcript)
    # Stitch transcripts, removing duplicate overlap lines
    stitched = []
    prev_lines = set()
    for t in transcripts:
        lines = t.strip().split('\n')
        # Remove lines that are already in prev_lines (from overlap)
        new_lines = [line for line in lines if line not in prev_lines]
        stitched.extend(new_lines)
        prev_lines.update(new_lines)
    full_transcript = '\n'.join(stitched)
    with open(transcript_filename, 'w', encoding='utf-8') as f:
        f.write(full_transcript)
    logger.info(f"Stitched transcript saved to {transcript_filename}")
    return full_transcript


def transcribe_audio(audio_path: str, transcript_filename: str) -> str:
    """Transcribe audio using Gemini 2.0 Flash API with speaker diarization."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not found in environment variables. Please check your .env file.")
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    if not os.path.exists(audio_path):
        print(f"[ERROR] Audio file not found: {audio_path}")
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    try:
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()
    except Exception as e:
        print(f"[ERROR] Failed to read audio file: {e}")
        raise
    if not audio_data:
        print("[ERROR] Audio file is empty")
        raise ValueError("Audio file is empty")
    try:
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    except Exception as e:
        print(f"[ERROR] Failed to encode audio file: {e}")
        raise
    prompt = ("""
        You are a professional audio transcriptionist. Your task is to:
        1. Transcribe the audio with high accuracy.
        2. Identify and label each speaker (e.g., 'Speaker 1', 'Speaker 2').
        3. Format each line as: [MM:SS] Speaker Name: Text
        4. Add a new line between different speakers.
        5. If it's a single speaker, break the text into logical paragraphs with timestamps.
    """)
    content_parts = [
        {"text": prompt},
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
        print(f"[ERROR] Failed to get response from Gemini API: {e}")
        raise
    if not response or not response.text:
        print("[ERROR] Empty response from Gemini API")
        raise ValueError("Empty response from Gemini API")
    logger.info("Successfully received transcript from Gemini API.")
    try:
        with open(transcript_filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
    except Exception as e:
        print(f"[ERROR] Failed to save transcript to file: {e}")
        raise
    logger.info(f"Transcript saved to {transcript_filename}")
    return response.text


def get_youtube_description(video_url: str) -> Optional[str]:
    """Fetch video description using yt-dlp."""
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info.get('description')
    except Exception as e:
        logger.error(f"Error fetching description: {e}")
        return None


if __name__ == "__main__":
    main()
