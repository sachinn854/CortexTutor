"""
Utility functions and helpers.
Common functions used across the application.
"""

import re
from typing import Optional
from urllib.parse import urlparse, parse_qs
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def validate_youtube_url(url: str) -> bool:
    """
    Validate if a URL is a valid YouTube URL.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if valid YouTube URL
    """
    youtube_patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/embed/[\w-]+'
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    
    # Check if it's just a video ID (11 characters)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return True
    
    return False


def extract_video_id_safe(url: str) -> Optional[str]:
    """
    Safely extract video ID from YouTube URL.
    
    Args:
        url: YouTube URL
        
    Returns:
        str: Video ID or None if extraction fails
    """
    try:
        # Pattern 1: youtube.com/watch?v=VIDEO_ID
        if "youtube.com/watch" in url:
            parsed = urlparse(url)
            video_id = parse_qs(parsed.query).get('v')
            if video_id:
                return video_id[0]
        
        # Pattern 2: youtu.be/VIDEO_ID
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        
        # Pattern 3: youtube.com/embed/VIDEO_ID
        if "youtube.com/embed/" in url:
            return url.split("embed/")[1].split("?")[0]
        
        # Pattern 4: Just the video ID
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting video ID: {str(e)}")
        return None


def format_error_response(
    error_type: str,
    message: str,
    details: Optional[dict] = None
) -> dict:
    """
    Format error response consistently.
    
    Args:
        error_type: Type of error (e.g., "ValidationError", "NotFound")
        message: Error message
        details: Additional error details
        
    Returns:
        dict: Formatted error response
    """
    response = {
        "status": "error",
        "error_type": error_type,
        "message": message
    }
    
    if details:
        response["details"] = details
    
    return response


def format_success_response(
    message: str,
    data: Optional[dict] = None
) -> dict:
    """
    Format success response consistently.
    
    Args:
        message: Success message
        data: Response data
        
    Returns:
        dict: Formatted success response
    """
    response = {
        "status": "success",
        "message": message
    }
    
    if data:
        response["data"] = data
    
    return response


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with consistent formatting.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)


def log_function_call(func_name: str, **kwargs):
    """
    Log function call with parameters.
    
    Args:
        func_name: Function name
        **kwargs: Function parameters
    """
    params = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"Calling {func_name}({params})")


def log_error(error: Exception, context: str = ""):
    """
    Log error with context.
    
    Args:
        error: Exception object
        context: Additional context
    """
    error_msg = f"Error in {context}: {str(error)}" if context else str(error)
    logger.error(error_msg, exc_info=True)


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Calculate estimated reading time for text.
    
    Args:
        text: Text to analyze
        words_per_minute: Average reading speed
        
    Returns:
        int: Estimated reading time in minutes
    """
    word_count = len(text.split())
    reading_time = word_count / words_per_minute
    return max(1, round(reading_time))


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        list: List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


# Test function
def test_helpers():
    """Test helper functions."""
    print("\n" + "="*60)
    print("Testing Helper Functions")
    print("="*60)
    
    # Test URL validation
    print("\n1. Testing URL validation:")
    test_urls = [
        "https://www.youtube.com/watch?v=aircAruvnKk",
        "https://youtu.be/aircAruvnKk",
        "aircAruvnKk",
        "https://google.com",
        "invalid"
    ]
    
    for url in test_urls:
        is_valid = validate_youtube_url(url)
        video_id = extract_video_id_safe(url)
        print(f"  {url[:40]:40} -> Valid: {is_valid}, ID: {video_id}")
    
    # Test error formatting
    print("\n2. Testing error formatting:")
    error = format_error_response(
        "ValidationError",
        "Invalid input",
        {"field": "url"}
    )
    print(f"  {error}")
    
    # Test success formatting
    print("\n3. Testing success formatting:")
    success = format_success_response(
        "Operation completed",
        {"video_id": "abc123"}
    )
    print(f"  {success}")
    
    # Test text truncation
    print("\n4. Testing text truncation:")
    long_text = "This is a very long text that needs to be truncated for display purposes."
    truncated = truncate_text(long_text, 30)
    print(f"  Original: {long_text}")
    print(f"  Truncated: {truncated}")
    
    # Test filename sanitization
    print("\n5. Testing filename sanitization:")
    bad_filename = "My Video: Part 1/2 <test>.mp4"
    sanitized = sanitize_filename(bad_filename)
    print(f"  Original: {bad_filename}")
    print(f"  Sanitized: {sanitized}")
    
    # Test reading time
    print("\n6. Testing reading time calculation:")
    sample_text = " ".join(["word"] * 500)
    reading_time = calculate_reading_time(sample_text)
    print(f"  Text length: 500 words")
    print(f"  Reading time: {reading_time} minutes")
    
    # Test list chunking
    print("\n7. Testing list chunking:")
    test_list = list(range(1, 11))
    chunks = chunk_list(test_list, 3)
    print(f"  Original: {test_list}")
    print(f"  Chunks (size 3): {chunks}")
    
    print("\n" + "="*60)
    print("✅ All helper tests passed!")
    print("="*60)


if __name__ == "__main__":
    test_helpers()
