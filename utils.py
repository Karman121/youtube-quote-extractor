import re
import logging

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', filename)


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