"""
Study Material Generator - Auto-generates learning materials from videos.
Creates summaries, flashcards, and key takeaways.
"""

from typing import Dict, List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm import get_llm
from app.core.config import settings
import json
import os
import re


# MCQ with Options Prompt
MCQ_WITH_OPTIONS_PROMPT = """You are an expert question creator. Generate multiple choice questions from this transcript.

VIDEO TRANSCRIPT:
{transcript}

Create exactly 5 high-quality MCQ questions with 4 options each.

Respond with ONLY this JSON format, no other text:
[
  {{
    "question": "The question text here?",
    "options": ["Option A (wrong)", "Option B (wrong)", "Option C (correct)", "Option D (wrong)"],
    "correct_answer": 2,
    "explanation": "Why this is correct"
  }}
]

Requirements:
- correct_answer is the INDEX (0-3) of the correct option
- Make options plausible but clearly distinguishable
- All questions should test understanding of key concepts
- Return ONLY valid JSON array"""


# Detailed Notes Prompt
DETAILED_NOTES_PROMPT = """You are an expert educational content writer. Create comprehensive study notes from this transcript.

VIDEO TRANSCRIPT:
{transcript}

Create detailed, well-structured study notes covering ALL major topics.

Respond with ONLY this JSON format, no other text:
{{
  "title": "Topic Title",
  "overview": "2-3 sentence overview",
  "sections": [
    {{
      "heading": "Section heading",
      "content": "Detailed explanation of this section",
      "key_points": ["point 1", "point 2", "point 3"]
    }}
  ],
  "summary": "Final summary of the lecture",
  "important_concepts": ["concept 1", "concept 2", "concept 3"]
}}

Requirements:
- Cover all major topics from the transcript
- Include practical examples
- Make it suitable for exam preparation
- Keep output concise enough to remain valid JSON:
    - sections: 4 to 6
    - each section content: 70-120 words
    - each section key_points: exactly 3 items
    - important_concepts: 6 to 10 items
- Return ONLY valid JSON"""


DETAILED_NOTES_TEXT_PROMPT = """You are an expert educational tutor.

FULL LECTURE CONTEXT:
{transcript}

Task:
Generate detailed study notes from the full lecture context.

Output format (Markdown text only, NOT JSON):
- Start with: # 📝 Study Notes
- Add a short title line: ## <Lecture Topic>
- Add an overview paragraph (3-4 sentences)
- Add 4-6 sections, each with:
  - ### <Section Heading>
  - Explanation paragraph (5-8 lines)
  - Key points list (3 bullets)
- Add final section: ## Summary

Rules:
- Cover the complete lecture flow from beginning to end
- Use only context provided above
- Keep it clear for exam revision
- Return plain markdown text only
"""


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
FLASHCARD_PROMPT = """You are an educational content creator. Create quality flashcards from this transcript.

VIDEO TRANSCRIPT:
{transcript}

Create exactly 8-10 flashcards as a JSON array.

Respind with ONLY this JSON format, no other text:
[
  {{
    "question": "Clear question testing a concept",
    "answer": "Concise answer in 2-3 sentences",
    "timestamp": "MM:SS"
  }}
]

Return ONLY the JSON array, nothing else. Make sure it is valid JSON."""


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
        
        print(f"🔍 Summary response (first 200 chars): {response[:200]}")
        
        # Clean response - extract JSON if wrapped
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response
        
        # Try to parse JSON
        try:
            summary_data = json.loads(json_str)
            print(f"✅ Summary parsed successfully")
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}. Using fallback.")
            # Fallback if LLM doesn't return valid JSON
            summary_data = {
                "overview": "This video covers key concepts related to the topic.",
                "key_points": ["Concept 1", "Concept 2", "Concept 3"],
                "prerequisites": ["Basic understanding"],
                "learning_outcomes": ["Understanding of main concepts"]
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
        
        print(f"🔍 Raw LLM response for flashcards:")
        print(f"Response type: {type(response)}")
        print(f"Response content: {response[:500]}...")  # First 500 chars
        
        # Clean up response - extract JSON if wrapped in text
        def extract_json_array_from_response(text: str) -> str:
            """Extract JSON array from potentially messy response"""
            import re
            # Remove markdown code blocks if present
            text = text.replace("```json", "").replace("```", "")
            # Look for JSON array pattern - more flexible
            json_match = re.search(r'\s*\[\s*.*?\s*\]\s*', text, re.DOTALL)
            if json_match:
                return json_match.group(0).strip()
            return text.strip()
        
        cleaned_response = extract_json_array_from_response(response)
        
        # Try to parse JSON
        try:
            flashcards = json.loads(cleaned_response)
            if not isinstance(flashcards, list):
                print(f"⚠️ Response is not a list, type: {type(flashcards)}")
                flashcards = []
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Cleaned response: {cleaned_response}")
            print(f"Original response: {response}")
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
    os.makedirs(settings.study_materials_path, exist_ok=True)
    materials_dir = os.path.join(settings.study_materials_path, video_id)
    os.makedirs(materials_dir, exist_ok=True)
    
    # Save as JSON
    filepath = os.path.join(materials_dir, "materials.json")
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
    os.makedirs(settings.study_materials_path, exist_ok=True)
    filepath = os.path.join(settings.study_materials_path, video_id, "materials.json")
    
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


def _chunk_text(text: str, chunk_size: int = 3500, overlap: int = 350) -> List[str]:
    """Split long text into overlapping chunks for map-reduce generation."""
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    chunks = []
    start = 0
    text_len = len(cleaned)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(cleaned[start:end])
        if end == text_len:
            break
        start = max(end - overlap, 0)

    return chunks


def _extract_balanced_json(text: str, opener: str) -> str:
    """Extract first balanced JSON object/array from model output."""
    if not text:
        return ""

    text = text.replace("```json", "").replace("```", "")
    closer = "}" if opener == "{" else "]"
    start_idx = text.find(opener)
    if start_idx == -1:
        return text.strip()

    depth = 0
    in_string = False
    escaped = False

    for idx in range(start_idx, len(text)):
        ch = text[idx]

        if escaped:
            escaped = False
            continue

        if ch == "\\":
            escaped = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[start_idx:idx + 1].strip()

    return text[start_idx:].strip()


def _safe_json_loads(text: str, expect: str):
    """Parse JSON safely and return expected fallback type on failure."""
    try:
        parsed = json.loads(text)
        if expect == "list":
            return parsed if isinstance(parsed, list) else []
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return [] if expect == "list" else {}


def _build_global_context(transcript_text: str, video_id: str) -> str:
    """Create compressed full-transcript context by summarizing each chunk."""
    chunks = _chunk_text(transcript_text)
    if not chunks:
        return ""

    llm = get_llm()
    map_prompt = PromptTemplate(
        template=(
            "You are helping build study materials.\n"
            "Summarize this transcript chunk into 6 concise bullet points with factual details.\n"
            "Keep names, formulas, definitions, and examples if present.\n\n"
            "CHUNK {index}/{total}:\n{chunk}\n\n"
            "Return plain bullet points only."
        ),
        input_variables=["index", "total", "chunk"]
    )
    map_chain = map_prompt | llm | StrOutputParser()

    summaries = []
    total = len(chunks)
    print(f"🧩 Building full-context summary from {total} chunks for {video_id}")

    for idx, chunk in enumerate(chunks, 1):
        try:
            chunk_summary = map_chain.invoke({
                "index": idx,
                "total": total,
                "chunk": chunk
            })
            summaries.append(f"[Chunk {idx}]\n{chunk_summary}")
        except Exception as e:
            print(f"⚠️ Chunk {idx} summarization failed: {e}")

    return "\n\n".join(summaries)


def _build_fallback_notes_from_context(full_context: str, video_id: str) -> Dict:
    """Create deterministic fallback notes from chunk summaries when JSON parse fails."""
    sections = []
    concepts = []

    chunk_blocks = [block.strip() for block in full_context.split("\n\n") if block.strip()]
    current_heading = ""
    current_lines = []

    for block in chunk_blocks:
        if block.startswith("[Chunk "):
            if current_heading and current_lines:
                joined = "\n".join(current_lines).strip()
                key_points = [
                    line.lstrip("-• ").strip()
                    for line in current_lines
                    if line.strip().startswith(("-", "•"))
                ][:3]
                if not key_points:
                    key_points = ["Key idea from this lecture part"]

                sections.append({
                    "heading": current_heading,
                    "content": joined[:900],
                    "key_points": key_points
                })

                for point in key_points:
                    if point not in concepts:
                        concepts.append(point)

            current_heading = block.replace("[", "").replace("]", "")
            current_lines = []
        else:
            current_lines.append(block)

    if current_heading and current_lines:
        joined = "\n".join(current_lines).strip()
        key_points = [
            line.lstrip("-• ").strip()
            for line in current_lines
            if line.strip().startswith(("-", "•"))
        ][:3]
        if not key_points:
            key_points = ["Key idea from this lecture part"]

        sections.append({
            "heading": current_heading,
            "content": joined[:900],
            "key_points": key_points
        })

        for point in key_points:
            if point not in concepts:
                concepts.append(point)

    sections = sections[:6]
    concepts = concepts[:10]

    return {
        "title": "Lecture Notes",
        "overview": "These notes summarize the complete lecture context in structured form.",
        "sections": sections,
        "summary": "The lecture has been converted into chunk-based structured notes to preserve full coverage.",
        "important_concepts": concepts
    }


def generate_mcqs_with_options(transcript_text: str, video_id: str) -> List[Dict]:
    """
    Generate MCQ questions with multiple choice options from transcript.
    
    Args:
        transcript_text: Full transcript text
        video_id: Video ID
        
    Returns:
        List of MCQ dicts with options
    """
    print(f"\n📋 Generating MCQs with options for {video_id}...")
    
    try:
        full_context = _build_global_context(transcript_text, video_id)
        if not full_context:
            return []

        llm = get_llm()
        prompt = PromptTemplate(
            template=MCQ_WITH_OPTIONS_PROMPT,
            input_variables=["transcript"]
        )
        chain = prompt | llm | StrOutputParser()

        response = chain.invoke({"transcript": full_context})
        print(f"🔍 MCQ response (first 300 chars): {response[:300]}")

        json_str = _extract_balanced_json(response, "[")
        mcqs = _safe_json_loads(json_str, "list")

        valid_mcqs = []
        for item in mcqs:
            if not isinstance(item, dict):
                continue
            options = item.get("options", [])
            correct_answer = item.get("correct_answer", -1)
            if isinstance(options, list) and len(options) == 4 and isinstance(correct_answer, int):
                valid_mcqs.append(item)

        print(f"✅ Generated {len(valid_mcqs)} MCQs with options")
        return valid_mcqs[:5]
        
    except Exception as e:
        print(f"❌ MCQ generation failed: {str(e)}")
        return []


def generate_detailed_notes_text(transcript_text: str, video_id: str) -> str:
    """
    Generate detailed study notes as plain markdown text.

    Args:
        transcript_text: Full transcript text
        video_id: Video ID

    Returns:
        Markdown notes text
    """
    print(f"\n📖 Generating detailed notes text for {video_id}...")

    try:
        full_context = _build_global_context(transcript_text, video_id)
        if not full_context:
            return "# 📝 Study Notes\n\n⚠️ Could not build lecture context for notes generation."

        llm = get_llm()
        prompt = PromptTemplate(
            template=DETAILED_NOTES_TEXT_PROMPT,
            input_variables=["transcript"]
        )
        chain = prompt | llm | StrOutputParser()

        notes_text = chain.invoke({"transcript": full_context}).strip()
        if not notes_text:
            return "# 📝 Study Notes\n\n⚠️ Notes generation returned empty output."

        if "# 📝 Study Notes" not in notes_text:
            notes_text = "# 📝 Study Notes\n\n" + notes_text

        print(f"✅ Generated notes text ({len(notes_text)} chars)")
        return notes_text

    except Exception as e:
        print(f"❌ Notes text generation failed: {str(e)}")
        return "# 📝 Study Notes\n\n⚠️ Error generating notes. Please try again."


