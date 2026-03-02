"""
Quick script to view full transcript with timestamps.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.youtube_loader import load_youtube_transcript

# Load the transcript
video_url = "https://www.youtube.com/watch?v=aircAruvnKk"
result = load_youtube_transcript(video_url)

print("\n" + "="*80)
print(f"VIDEO: {result['video_url']}")
print(f"DURATION: {result['total_duration']}")
print(f"SEGMENTS: {len(result['transcript'])}")
print("="*80)

# Option 1: Show all segments
print("\n--- FULL TRANSCRIPT WITH TIMESTAMPS ---\n")
for i, segment in enumerate(result['transcript'], 1):
    print(f"{i}. [{segment['timestamp']}] {segment['text']}")
    if i % 20 == 0:  # Pause every 20 lines
        input("\nPress Enter to continue...")

# Option 2: Show full text (no timestamps)
print("\n\n" + "="*80)
print("--- FULL TEXT (NO TIMESTAMPS) ---")
print("="*80)
print(result['full_text'])
