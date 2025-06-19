import os
import re
import logging
from typing import Optional
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
from config import (
    DEFAULT_SETTINGS, 
    get_quote_extraction_prompt,
    CHUNKED_TRANSCRIPTION_PROMPT,
    ERROR_MESSAGES
)

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(DEFAULT_SETTINGS["retry_attempts"]), 
       wait=wait_exponential(multiplier=1, min=4, max=10))
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
    if not api_key:
        raise ValueError(ERROR_MESSAGES["gemini_api_key_missing"])
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(DEFAULT_SETTINGS["gemini_model"])
    
    focus_instruction = (
        f"The user is particularly interested in quotes related to: '{user_description}'"
        if user_description else ""
    )
    
    prompt = get_quote_extraction_prompt(
        focus_instruction=focus_instruction,
        video_description=video_description or "",
        transcript_segment=transcript_segment,
        timestamp=timestamp
    )
    
    logger.info(f"Extracting quote for timestamp {timestamp}...")
    response = model.generate_content(prompt)
    return f"[{timestamp}]\n{response.text.strip()}"

@sleep_and_retry
@limits(calls=DEFAULT_SETTINGS["rate_limit_calls"], 
        period=DEFAULT_SETTINGS["rate_limit_period"])
@retry(stop=stop_after_attempt(DEFAULT_SETTINGS["retry_attempts"]), 
       wait=wait_exponential(multiplier=1, min=4, max=10))
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
@limits(calls=DEFAULT_SETTINGS["rate_limit_calls"], 
        period=DEFAULT_SETTINGS["rate_limit_period"])
@retry(stop=stop_after_attempt(DEFAULT_SETTINGS["retry_attempts"]), 
       wait=wait_exponential(multiplier=1, min=4, max=10))
def process_file_with_retry(chat_session, file):
    """Process file with Gemini with retry logic."""
    try:
        logger.debug(f"Processing: {file.display_name}")
        response = chat_session.send_message(CHUNKED_TRANSCRIPTION_PROMPT)
        return response
    except Exception as e:
        logger.error(f"Processing failed for {file.display_name}: {str(e)}")
        raise

def extract_youtube_link(text: str) -> Optional[str]:
    youtube_pattern = (
        r'@?(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)' 
        r'[a-zA-Z0-9_-]+(?:\?[^&\s]*)?)'
    )
    match = re.search(youtube_pattern, text)
    return match.group(1) if match else None

def extract_video_id(url: str) -> Optional[str]:
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

def get_youtube_description(video_url: str) -> Optional[str]:
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info.get('description')
    except Exception as e:
        logger.error(f"Error fetching description: {e}")
        return None 