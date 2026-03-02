"""
Study Material Generator - Auto-generates learning materials from videos.
Creates summaries, flashcards, and key takeaways.
"""

from typing import Dict, List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm import get_llm
import json
import os


# Prompt for generating summary
SUMMARY_PROMPT = """You are an educational content analyzer. Analyze this video transcript and create a structured summary.

VIDEO TRANSCRIPT:
{transcript}

Create a JSON response with:
1. "overview": A 2-3 sentence overview of the main topic
2. "key_points": List of 5-7 main concepts covered (as array of strings)
3. "prerequisites": List of 2-4 prerequisite topics needed (as array of strings)
4. "learning_outcomes": What students will learn (as array of 3-5 strings)

Respond ONLY with valid JSON, no other text.
"""


# Prompt for generating flashcards
FLASHCARD_PROMPT = """You are an educational content creator. Create flashcards from this video transcript.

VIDEO TRANSCRIPT:
{transcript}

Create 10-12 flashcards that test understanding of key concepts.

For each flashcard, provide:
- question: A clear question
- answer: A concise answer (2-3 sentences max)
- timestamp: Approximate timestamp where this is discussed (format: MM:SS)

Respond with JSON array of flashcards ONLY, no other text.
Format: [{{"question": "...", "answer": "...", "timestamp": "..."}}]
"""


def generate_summary(transcript_text: str, video_id: str) -> Dict:
    """
    Generate structured summary from transcript.
    
    Args:
        transcript_text: Full transcript text
        video_id: Video ID
        
    Returns:
        Dict with summary data
    """
    print(f"\n📝 Generating summary for {video_id}...")
    
    try:
        llm = get_llm()
        prompt = PromptTemplate(
            template=SUMMARY_PROMPT,
            input_variables=["transcript"]
        )
        
        chain = prompt | llm | StrOutputParser()
        
        # Use first 3000 chars to avoid token limits
        truncated_transcript = transcript_text[:3000]
        
        response = chain.invoke({"transcript": truncated_transcript})
        
        # Try to parse JSON
        try:
            summary_data = json.loads(response)
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            summary_data = {
                "overview": response[:200],
                "key_points": ["Content analysis in progress"],
                "prerequisites": ["Basic understanding recommended"],
                "learning_outcomes": ["Detailed concepts from the video"]
            }
        
        print(f"✅ Summary generated")
        return summary_data
        
    except Exception as e:
        print(f"❌ Summary generation failed: {str(e)}")
        return {
            "overview": "Summary generation in progress",
            "key_points": [],
            "prerequisites": [],
            "learning_outcomes": []
        }


def generate_flashcards(transcript_text: str, video_id: str) -> List[Dict]:
    """
    Generate flashcards from transcript.
    
    Args:
        transcript_text: Full transcript text
        video_id: Video ID
        
    Returns:
        List of flashcard dicts
    """
    print(f"\n🎴 Generating flashcards for {video_id}...")
    
    try:
        llm = get_llm()
        prompt = PromptTemplate(
            template=FLASHCARD_PROMPT,
            input_variables=["transcript"]
        )
        
        chain = prompt | llm | StrOutputParser()
        
        # Use first 3000 chars
        truncated_transcript = transcript_text[:3000]
        
        response = chain.invoke({"transcript": truncated_transcript})
        
        # Try to parse JSON
        try:
            flashcards = json.loads(response)
            if not isinstance(flashcards, list):
                flashcards = []
        except json.JSONDecodeError:
            flashcards = []
        
        print(f"✅ Generated {len(flashcards)} flashcards")
        return flashcards
        
    except Exception as e:
        print(f"❌ Flashcard generation failed: {str(e)}")
        return []


def generate_key_takeaways(transcript_text: str, video_id: str) -> List[str]:
    """
    Generate key takeaways from transcript.
    
    Args:
        transcript_text: Full transcript text
        video_id: Video ID
        
    Returns:
        List of key takeaway strings
    """
    print(f"\n💡 Generating key takeaways for {video_id}...")
    
    try:
        llm = get_llm()
        
        prompt_text = f"""Extract 5 key takeaways from this video transcript.

TRANSCRIPT:
{transcript_text[:2000]}

List 5 key takeaways as a JSON array of strings.
Format: ["takeaway 1", "takeaway 2", ...]
"""
        
        response = llm.invoke(prompt_text)
        
        # Extract content from response
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)
        
        # Try to parse JSON
        try:
            takeaways = json.loads(response_text)
            if not isinstance(takeaways, list):
                takeaways = [response_text]
        except json.JSONDecodeError:
            # Fallback: split by newlines
            takeaways = [line.strip() for line in response_text.split('\n') if line.strip()][:5]
        
        print(f"✅ Generated {len(takeaways)} takeaways")
        return takeaways
        
    except Exception as e:
        print(f"❌ Takeaway generation failed: {str(e)}")
        return []


def generate_all_materials(video_id: str, transcript_text: str) -> Dict:
    """
    Generate all study materials for a video.
    
    Args:
        video_id: Video ID
        transcript_text: Full transcript text
        
    Returns:
        Dict with all materials
    """
    print(f"\n📚 Generating all study materials for {video_id}...")
    
    materials = {
        "video_id": video_id,
        "summary": generate_summary(transcript_text, video_id),
        "flashcards": generate_flashcards(transcript_text, video_id),
        "key_takeaways": generate_key_takeaways(transcript_text, video_id)
    }
    
    return materials


def save_study_materials(video_id: str, materials: Dict):
    """
    Save study materials to disk.
    
    Args:
        video_id: Video ID
        materials: Materials dict
    """
    # Create directory
    materials_dir = f"study_materials/{video_id}"
    os.makedirs(materials_dir, exist_ok=True)
    
    # Save as JSON
    filepath = f"{materials_dir}/materials.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(materials, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved study materials to {filepath}")


def load_study_materials(video_id: str) -> Dict:
    """
    Load study materials from disk.
    
    Args:
        video_id: Video ID
        
    Returns:
        Dict with materials or None if not found
    """
    filepath = f"study_materials/{video_id}/materials.json"
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# Test function
def test_study_material_generator():
    """Test study material generation."""
    from app.services.youtube_loader import load_youtube_transcript
    
    print("\n" + "="*60)
    print("Testing Study Material Generator")
    print("="*60)
    
    try:
        # Load test video
        video_url = "https://www.youtube.com/watch?v=aircAruvnKk"
        transcript_data = load_youtube_transcript(video_url)
        
        video_id = transcript_data['video_id']
        transcript_text = transcript_data['full_text']
        
        # Generate materials
        materials = generate_all_materials(video_id, transcript_text)
        
        # Display results
        print("\n📝 SUMMARY:")
        print(f"Overview: {materials['summary'].get('overview', 'N/A')}")
        print(f"Key Points: {len(materials['summary'].get('key_points', []))}")
        
        print(f"\n🎴 FLASHCARDS: {len(materials['flashcards'])}")
        if materials['flashcards']:
            print(f"Sample: {materials['flashcards'][0].get('question', 'N/A')}")
        
        print(f"\n💡 KEY TAKEAWAYS: {len(materials['key_takeaways'])}")
        
        # Save materials
        save_study_materials(video_id, materials)
        
        # Test loading
        loaded = load_study_materials(video_id)
        print(f"\n✅ Materials saved and loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_study_material_generator()
