"""
YouTube transcript loader with timestamp support.
Fetches transcripts and preserves timing information for deep linking.
Falls back to yt-dlp when youtube-transcript-api is blocked by the host.
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
import json
import urllib.request


def extract_video_id(url: str) -> str:
    if "youtube.com/watch" in url:
        parsed = urlparse(url)
        video_id = parse_qs(parsed.query).get('v')
        if video_id:
            return video_id[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    if "youtube.com/embed/" in url:
        return url.split("embed/")[1].split("?")[0]
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    raise ValueError(f"Could not extract video ID from URL: {url}")


def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def create_youtube_url_with_timestamp(video_id: str, start_time: float) -> str:
    return f"https://www.youtube.com/watch?v={video_id}&t={int(start_time)}s"


def _load_transcript_with_ytdlp(video_id: str) -> Dict:
    """
    Fallback transcript loader using yt-dlp.
    yt-dlp uses YouTube's Innertube API which has better availability
    from cloud/hosted environments where direct YouTube access is blocked.
    """
    import yt_dlp
    import concurrent.futures

    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"   Trying yt-dlp fallback for {video_id}...")

    ydl_opts = {
        "skip_download": True,
        "writesubtitles": False,
        "writeautomaticsub": False,
        "subtitleslangs": ["en", "hi", "en-US", "en-GB"],
        "subtitlesformat": "json3",
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 20,
        # Use Innertube API — avoids normal web scraping restrictions
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }

    def _run_ydl():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    # Run in thread with 45-second hard timeout so we don't block the event loop
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_ydl)
        try:
            info = future.result(timeout=45)
        except concurrent.futures.TimeoutError:
            raise ConnectionError("yt-dlp timed out after 45 seconds")

    if not info:
        raise ConnectionError("yt-dlp could not retrieve video info")

    # Find caption URL — prefer manual en, then auto en, then any
    subtitles = info.get("subtitles", {})
    auto_subtitles = info.get("automatic_captions", {})

    caption_url = None
    for lang_pool in [subtitles, auto_subtitles]:
        for lang in ["en", "en-US", "en-GB", "hi"]:
            if lang in lang_pool:
                for fmt in lang_pool[lang]:
                    if fmt.get("ext") == "json3":
                        caption_url = fmt["url"]
                        break
                if caption_url:
                    break
        if caption_url:
            break

    # Last resort: first available language + format
    if not caption_url:
        for lang_pool in [subtitles, auto_subtitles]:
            for lang, fmts in lang_pool.items():
                for fmt in fmts:
                    if fmt.get("ext") == "json3":
                        caption_url = fmt["url"]
                        break
                if caption_url:
                    break
            if caption_url:
                break

    if not caption_url:
        raise ValueError("No captions available via yt-dlp for this video.")

    print(f"   Fetching captions from CDN...")
    req = urllib.request.Request(caption_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")

    data = json.loads(raw)
    events = data.get("events", [])

    processed_transcript = []
    full_text_parts = []

    for event in events:
        segs = event.get("segs")
        if not segs:
            continue
        text = "".join(s.get("utf8", "") for s in segs).strip()
        if not text or text == "\n":
            continue
        start_ms = event.get("tStartMs", 0)
        dur_ms = event.get("dDurationMs", 0)
        start = start_ms / 1000.0
        duration = dur_ms / 1000.0

        processed_transcript.append({
            "text": text,
            "start": start,
            "duration": duration,
            "timestamp": format_timestamp(start),
            "url": create_youtube_url_with_timestamp(video_id, start),
        })
        full_text_parts.append(text)

    if not processed_transcript:
        raise ValueError("yt-dlp returned empty transcript.")

    total_duration = 0.0
    if processed_transcript:
        last = processed_transcript[-1]
        total_duration = last["start"] + last["duration"]

    print(f"   ✅ yt-dlp loaded {len(processed_transcript)} segments")
    return {
        "video_id": video_id,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "transcript": processed_transcript,
        "full_text": " ".join(full_text_parts),
        "total_duration": total_duration,
    }


def load_youtube_transcript(
    url: str,
    languages: Optional[List[str]] = None
) -> Dict:
    """
    Load YouTube transcript with timestamps preserved.
    Tries youtube-transcript-api first; falls back to yt-dlp on network errors.
    """
    if languages is None:
        languages = ['en', 'hi', 'es', 'fr', 'de', 'pt', 'ja', 'ko', 'zh-Hans', 'zh-Hant']

    video_id = extract_video_id(url)
    print(f"📹 Loading transcript for video: {video_id}")

    # ── Primary: youtube-transcript-api ───────────────────────
    primary_error = None
    try:
        api = YouTubeTranscriptApi()
        transcript_data = None

        try:
            print(f"   Fetching transcript...")
            transcript_data = api.fetch(video_id, languages=languages)
            print(f"   ✅ Found transcript")
        except NoTranscriptFound:
            try:
                print(f"   Trying without language filter...")
                transcript_data = api.fetch(video_id)
                print(f"   ✅ Found transcript")
            except Exception as e:
                raise ValueError(
                    "No transcript available for this video. Make sure captions/subtitles are enabled."
                ) from e

        print(f"✅ Loaded {len(transcript_data)} segments")

        processed_transcript = []
        full_text_parts = []

        for entry in transcript_data:
            text = entry.text.strip()
            start = entry.start
            duration = entry.duration
            processed_transcript.append({
                'text': text,
                'start': start,
                'duration': duration,
                'timestamp': format_timestamp(start),
                'url': create_youtube_url_with_timestamp(video_id, start)
            })
            full_text_parts.append(text)

        full_text = ' '.join(full_text_parts)
        total_duration = 0.0
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

    except (TranscriptsDisabled, VideoUnavailable) as e:
        # These mean the video itself has no captions — yt-dlp won't help either
        raise

    except RequestBlocked as e:
        print(f"   ⚠️  youtube-transcript-api blocked — trying yt-dlp fallback...")
        primary_error = e

    except (ConnectionError, OSError) as e:
        # SSL EOF, DNS failure, etc. — try yt-dlp
        print(f"   ⚠️  Network error ({type(e).__name__}) — trying yt-dlp fallback...")
        primary_error = e

    except Exception as e:
        err_str = str(e).lower()
        if any(x in err_str for x in ("ssl", "connection", "network", "unreachable", "timed out", "timeout")):
            print(f"   ⚠️  Connection issue — trying yt-dlp fallback...")
            primary_error = e
        else:
            print(f"❌ Error loading transcript: {str(e)}")
            raise

    # ── Fallback: yt-dlp ──────────────────────────────────────
    try:
        result = _load_transcript_with_ytdlp(video_id)
        print(f"📊 Total duration: {format_timestamp(result['total_duration'])}")
        return result
    except Exception as ytdlp_err:
        print(f"   ❌ yt-dlp fallback also failed: {ytdlp_err}")
        # Re-raise a clear message so the API returns a helpful 503
        raise ConnectionError(
            "YouTube is unreachable from this runtime. Use /api/ingest/text as a fallback."
        ) from primary_error
