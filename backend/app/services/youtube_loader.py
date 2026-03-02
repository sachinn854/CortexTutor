"""
YouTube transcript loader with timestamp support.
Fetches transcripts and preserves timing information for deep linking.
"""

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    RequestBlocked
)
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs
import re


def extract_video_id(url: str) -> str:
    """
    Extract video ID from various YouTube URL formats.
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    
    Args:
        url: YouTube video URL
        
    Returns:
        str: Video ID
        
    Raises:
        ValueError: If URL is invalid or video ID cannot be extracted
    """
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
    
    raise ValueError(f"Could not extract video ID from URL: {url}")


def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to MM:SS or HH:MM:SS format.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Formatted timestamp
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def create_youtube_url_with_timestamp(video_id: str, start_time: float) -> str:
    """
    Create a YouTube URL with timestamp parameter.
    
    Args:
        video_id: YouTube video ID
        start_time: Start time in seconds
        
    Returns:
        str: YouTube URL with &t= parameter
    """
    return f"https://www.youtube.com/watch?v={video_id}&t={int(start_time)}s"


def load_youtube_transcript(
    url: str,
    languages: Optional[List[str]] = None
) -> Dict:
    """
    Load YouTube transcript with timestamps preserved.
    
    Args:
        url: YouTube video URL or video ID
        languages: List of language codes to try (default: ['en', 'hi', 'es', 'fr', 'de'])
        
    Returns:
        Dict containing:
            - video_id: str
            - video_url: str
            - transcript: List[Dict] with 'text', 'start', 'duration', 'timestamp', 'url'
            - full_text: str (concatenated transcript)
            - total_duration: float
            
    Raises:
        ValueError: If video ID cannot be extracted
        TranscriptsDisabled: If transcripts are disabled for the video
        NoTranscriptFound: If no transcript in requested languages
        VideoUnavailable: If video is unavailable
    """
    if languages is None:
        # Try multiple languages by default
        languages = ['en', 'hi', 'es', 'fr', 'de', 'pt', 'ja', 'ko', 'zh-Hans', 'zh-Hant']
    
    try:
        # Extract video ID
        video_id = extract_video_id(url)
        print(f"📹 Loading transcript for video: {video_id}")
        
        # Fetch transcript using the correct API (v1.2.4)
        # Need to create an instance first with custom headers
        api = YouTubeTranscriptApi()
        transcript_data = None
        
        # Add custom headers to avoid blocking
        import requests
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        try:
            # Try to fetch with requested languages
            print(f"   Fetching transcript...")
            transcript_data = api.fetch(video_id, languages=languages)
            print(f"   ✅ Found transcript")
        except NoTranscriptFound:
            # Try without language filter
            try:
                print(f"   Trying without language filter...")
                transcript_data = api.fetch(video_id)
                print(f"   ✅ Found transcript")
            except Exception as e:
                print(f"   ❌ No transcript available: {str(e)}")
                raise NoTranscriptFound(
                    video_id,
                    "No transcript available for this video. Make sure captions/subtitles are enabled.",
                    languages
                )
        except Exception as e:
            if isinstance(e, (TranscriptsDisabled, VideoUnavailable)):
                raise
            print(f"   ❌ Error: {str(e)}")
            raise
        
        print(f"✅ Loaded {len(transcript_data)} segments")
        
        # Process transcript with timestamps
        processed_transcript = []
        full_text_parts = []
        
        for entry in transcript_data:
            # FetchedTranscriptSnippet object with attributes (not dict)
            text = entry.text.strip()
            start = entry.start
            duration = entry.duration
            
            # Create enriched entry with timestamp info
            processed_entry = {
                'text': text,
                'start': start,
                'duration': duration,
                'timestamp': format_timestamp(start),
                'url': create_youtube_url_with_timestamp(video_id, start)
            }
            
            processed_transcript.append(processed_entry)
            full_text_parts.append(text)
        
        # Combine all text
        full_text = ' '.join(full_text_parts)
        
        # Calculate total duration
        total_duration = 0
        if transcript_data:
            last_entry = transcript_data[-1]
            total_duration = last_entry.start + last_entry.duration
        
        result = {
            'video_id': video_id,
            'video_url': f"https://www.youtube.com/watch?v={video_id}",
            'transcript': processed_transcript,
            'full_text': full_text,
            'total_duration': total_duration
        }
        
        print(f"📊 Total duration: {format_timestamp(result['total_duration'])}")
        
        return result
        
    except RequestBlocked:
        raise Exception("YouTube is temporarily blocking requests. Please wait a few minutes and try again.")
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        raise
    except Exception as e:
        print(f"❌ Error loading transcript: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


# Test function
def test_youtube_loader():
    """Test the YouTube loader with a sample video."""
    # Using a popular educational video (3Blue1Brown)
    test_url = "https://www.youtube.com/watch?v=aircAruvnKk"
    
    try:
        print("\n" + "="*60)
        print("Testing YouTube Loader")
        print("="*60)
        
        result = load_youtube_transcript(test_url)
        
        print(f"\nVideo ID: {result['video_id']}")
        print(f"Total segments: {len(result['transcript'])}")
        print(f"Total duration: {format_timestamp(result['total_duration'])}")
        
        # Show first 3 segments
        print("\nFirst 3 segments:")
        for i, segment in enumerate(result['transcript'][:3]):
            print(f"\n[{segment['timestamp']}]")
            print(f"Text: {segment['text']}")
            print(f"URL: {segment['url']}")
        
        print("\n✅ YouTube loader test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    test_youtube_loader()
