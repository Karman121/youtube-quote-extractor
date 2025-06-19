import os
import yt_dlp
from typing import Optional, Tuple, List
from pydub import AudioSegment
from pydub.utils import mediainfo
import logging
from utils import sanitize_filename
from config import DEFAULT_SETTINGS, SUCCESS_MESSAGES

logger = logging.getLogger(__name__)

def download_audio(url: str, output_path: str = None) -> Optional[Tuple[str, str, str]]:
    """
    Downloads audio from a YouTube URL with correct caching and fallback logic.
    Returns (audio_path, title, description)
    """
    if output_path is None:
        output_path = DEFAULT_SETTINGS["output_directory"]
    
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
            logger.info(SUCCESS_MESSAGES["audio_exists"].format(expected_filepath))
            return expected_filepath, title, description
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': DEFAULT_SETTINGS["audio_quality"],
        }],
        'outtmpl': os.path.join(output_path, f"{sanitized_title}.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        logger.info(f"Downloading audio: {url}")
        try:
            ydl.download([url])
            logger.info(SUCCESS_MESSAGES["audio_downloaded"].format(expected_filepath))
            return expected_filepath, title, description
        except Exception as e:
            print(f"[ERROR] Failed to download audio: {e}")
            logger.error(f"Failed to download audio: {e}")
            return

def split_audio(audio_path, chunk_duration):
    """Split audio file into chunks of specified duration."""
    audio = AudioSegment.from_mp3(audio_path)
    duration_ms = len(audio)
    chunk_duration_ms = chunk_duration * 1000
    num_chunks = max(
        1, (duration_ms + chunk_duration_ms - 1) // chunk_duration_ms
    )
    logger.info(
        f"Audio duration: {duration_ms/1000:.2f}s, "
        f"splitting into {num_chunks} chunks"
    )
    chunks = []
    for i in range(num_chunks):
        start_ms = i * chunk_duration_ms
        end_ms = min((i + 1) * chunk_duration_ms, duration_ms)
        if i > 0:
            start_ms = max(0, start_ms - 10000)
        if i < num_chunks - 1:
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

def split_audio_chunks(audio_path: str, chunk_length_min: int = None, overlap_sec: int = None) -> List[Tuple[str, int]]:
    """
    Splits audio into chunks of chunk_length_min (in minutes) with overlap_sec (in seconds).
    Returns a list of (chunk_path, chunk_start_sec).
    """
    if chunk_length_min is None:
        chunk_length_min = DEFAULT_SETTINGS["chunk_length_minutes"]
    if overlap_sec is None:
        overlap_sec = DEFAULT_SETTINGS["overlap_seconds"]
    
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
        start_ms = end_ms - overlap_ms
        chunk_idx += 1
    return chunks

def get_audio_file_info(audio_path: str) -> Tuple[float, float]:
    """
    Returns (file_size_MB, duration_minutes) for the given audio file.
    """
    file_size_MB = os.path.getsize(audio_path) / (1024 * 1024)
    info = mediainfo(audio_path)
    duration_sec = float(info['duration'])
    duration_minutes = duration_sec / 60
    return file_size_MB, duration_minutes 