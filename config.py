"""
Configuration file for YouTube Quote Extractor
Contains default settings, prompts, and configuration parameters.
"""

# Default Settings
DEFAULT_SETTINGS = {
    # Audio processing
    "chunk_length_minutes": 30,
    "overlap_seconds": 30,
    "max_file_size_mb": 100,
    "max_duration_minutes": 50,
    
    # Context windows
    "default_context_after_seconds": 90,
    "default_context_before_seconds": 30,
    
    # API settings
    "gemini_model": "gemini-2.5-flash",
    "retry_attempts": 3,
    "rate_limit_calls": 1.8,
    "rate_limit_period": 1,
    
    # File settings
    "audio_quality": "192",
    "output_directory": ".",
}

# Transcription Prompt
TRANSCRIPTION_PROMPT = """
You are a professional audio transcriptionist. Your task is to:
1. Transcribe the audio with high accuracy.
2. Identify and label each speaker (e.g., 'Speaker 1', 'Speaker 2').
3. Format each line as: [MM:SS] Speaker Name: Text
4. Add a new line between different speakers.
5. If it's a single speaker, break the text into logical paragraphs with timestamps.
"""

# Quote Extraction Instructions (the 12 main instructions)
QUOTE_EXTRACTION_INSTRUCTIONS = [
    "Analyze the transcript, video description, and any context provided.",
    "Extract insightful, newsworthy quotes suitable for article use.",
    "**Crucial Task**: The user will provide a timestamp. Treat this timestamp as an **anchor point**. Your main goal is to find the complete conversational exchange (e.g., the full question and its full answer) that this anchor point falls within. You must read backwards from the anchor to find the beginning of the exchange.",
    "Speaker identification:\n   - Use names, roles, or the video description to confidently assign real names (e.g., \"Scott Agnes\", \"Tyrese Haliburton\") instead of generic labels.\n   - If unsure after checking context, use \"Unknown Speaker\".\n   - Be consistent with names across all quotes.",
    "In Q&A settings:\n   - Extract both the full question and the full answer as separate quotes, as they form a complete exchange.",
    "Quotes must be complete thoughts. If a statement starts or ends with a conjunction (e.g., 'and', 'but'), include the adjacent sentence(s) from the same speaker to make it a complete thought.",
    "Combine uninterrupted statements from a single speaker into one quote.",
    "Prioritize quotes that reveal new insights, strong opinions, or emotional stakes.",
    "DO NOT include filler words, small talk, or incomplete fragments.",
    "Format each quote as: `Speaker Name: \"The full quote.\"`",
    "Output ONLY the formatted quotes. Do not add any introductory text, summaries, or explanations.",
    "If a user description is provided, that is your primary focus for selecting what is \"newsworthy.\""
]

# Quote Extraction Base Prompt Template
QUOTE_EXTRACTION_PROMPT_TEMPLATE = """
You are a professional journalist extracting meaningful quotes for a news article. Your task is to:
{instructions}

**Context provided by the user (this is the most important input, if provided by user):**
{focus_instruction}

**Video Description (for overall context):**
{video_description}

**Transcript Segment (The user's point of interest is at or around timestamp {timestamp}):**
---
{transcript_segment}
---
"""

# Chunked Transcription Prompt (for file processing)
CHUNKED_TRANSCRIPTION_PROMPT = """
You are a professional audio transcriptionist. Your task is to:
1. Transcribe the audio with high accuracy
2. Identify and label each speaker by their name (e.g., 'Bye Manning', 'Brian Lewis')
3. Format each line as: '[MM:SS] Speaker Name: Text'
4. Include timestamps in MM:SS format, starting from the exact time provided
5. Keep complete sentences and thoughts together
6. Preserve the natural flow of conversation
7. If you can't identify a speaker, use 'Speaker 1', 'Speaker 2', etc.
8. Add a new line between different speakers
9. If it's a single speaker, break it into paragraphs.
10. IMPORTANT: Maintain exact timestamps as provided in the audio - do not adjust or estimate them.
"""

# User Input Prompts
USER_PROMPTS = {
    "input_instructions": "Paste your YouTube URL and timestamps (MM:SS - description) below. End input with an empty line:",
    "context_after": "Enter context window after timestamp (seconds, e.g. 90): ",
    "context_before": "Enter context window before timestamp (seconds, e.g. 30): ",
}

# Error Messages
ERROR_MESSAGES = {
    "no_url": "No YouTube URL found in your input. Please provide a valid URL.",
    "no_timestamps": "No timestamps found in your input. Please provide at least one timestamp in MM:SS or HH:MM:SS format.",
    "invalid_timestamp": "Invalid timestamp format: {}. Use MM:SS or HH:MM:SS.",
    "invalid_context": "Invalid input for context window. Please enter a number.",
    "download_failed": "Failed to download audio: {}",
    "transcript_failed": "Failed to read or write transcript file: {}",
    "empty_transcript": "Transcript is empty. Halting process.",
    "timestamp_beyond_end": "Timestamp {} is beyond the end of the transcript/audio (max is {}:{}). Skipping.",
    "segment_failed": "Failed to extract transcript segment for {}: {}",
    "quote_failed": "Failed to extract quote for {}: {}",
    "save_failed": "Failed to save quotes to file: {}",
    "gemini_api_key_missing": "GEMINI_API_KEY not found in environment variables. Please check your .env file.",
    "audio_file_not_found": "Audio file not found: {}",
    "audio_file_empty": "Audio file is empty",
    "gemini_api_failed": "Failed to get response from Gemini API: {}",
    "gemini_response_empty": "Empty response from Gemini API",
}

# Success Messages
SUCCESS_MESSAGES = {
    "audio_exists": "Found existing audio file: '{}'. Skipping download.",
    "transcript_exists": "Found existing transcript file: {}. Skipping transcription.",
    "audio_downloaded": "Audio downloaded: {}",
    "transcript_saved": "Transcript saved to {}",
    "quotes_saved": "All quotes saved to {}",
    "no_chunking": "No chunking needed.",
    "chunking_needed": "Chunking: duration > {}min or file size > {}MB. Splitting into {}min chunks with {}s overlap.",
}

# Analysis Prompt Template (for Ask Questions mode)
ANALYSIS_PROMPT_TEMPLATE = """
You are an expert analyst helping to extract insights from YouTube video content. 

**User's Question/Request:**
{user_question}

**Video Description (for context):**
{video_description}

**Full Transcript:**
---
{transcript}
---

Please provide a thorough analysis addressing the user's question. Be specific, cite relevant parts of the transcript, and provide actionable insights where appropriate.
"""

def get_quote_extraction_prompt(
    instructions: list = None,
    focus_instruction: str = "",
    video_description: str = "",
    transcript_segment: str = "",
    timestamp: str = ""
) -> str:
    """
    Generate the complete quote extraction prompt using the template and instructions.
    """
    if instructions is None:
        instructions = QUOTE_EXTRACTION_INSTRUCTIONS
    
    formatted_instructions = "\n".join(f"{i+1}. {instruction}" for i, instruction in enumerate(instructions))
    
    focus_text = focus_instruction if focus_instruction else "No specific topic was provided. Use your judgment to find the most newsworthy quote."
    video_desc = video_description if video_description else 'No description available.'
    
    return QUOTE_EXTRACTION_PROMPT_TEMPLATE.format(
        instructions=formatted_instructions,
        focus_instruction=focus_text,
        video_description=video_desc,
        transcript_segment=transcript_segment,
        timestamp=timestamp
    )

def get_analysis_prompt(
    user_question: str = "",
    video_description: str = "",
    transcript: str = ""
) -> str:
    """
    Generate the complete analysis prompt for the Ask Questions mode.
    """
    question_text = user_question if user_question else "Please provide a general analysis of this video content."
    video_desc = video_description if video_description else 'No description available.'
    transcript_text = transcript if transcript else 'No transcript available.'
    
    return ANALYSIS_PROMPT_TEMPLATE.format(
        user_question=question_text,
        video_description=video_desc,
        transcript=transcript_text
    ) 