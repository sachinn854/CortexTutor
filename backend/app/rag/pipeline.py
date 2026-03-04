"""
RAG Pipeline - Combines retriever and LLM for question answering.
Uses modern LangChain LCEL with intent-based routing.
Supports both Q&A mode and Lecture Summary mode.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import Dict, List
from app.core.llm import get_llm
from app.rag.retriever import create_retriever
from app.rag.vector_store import load_vector_store


# QA Prompt Template (for specific questions)
QA_PROMPT_TEMPLATE = """You are an expert AI tutor helping students understand educational content.

TRANSCRIPT CONTENT:
{context}

STUDENT'S QUESTION: {question}

INSTRUCTIONS:
- Answer clearly and directly - start immediately with the answer
- Base your answer strictly on the transcript content
- Do not add outside knowledge or related topics unless asked
- Do not add introductions, recaps, or closing remarks
- Do not repeat previous conversation unless directly relevant

TIMESTAMP HANDLING:
- If the user refers to a timestamp (e.g., "at 2:51" or "around 3:20"), locate and explain the concept discussed at that point
- Treat timestamps as references to specific content in the video
- Do not ask the user to restate the concept if it can be inferred from the transcript
- Interpret the user's intent - they want to know what was explained at that time

CRITICAL INSTRUCTION - RESPONSE LENGTH MATCHING:
You MUST analyze the question first and match your response length to the user's intent:

**SIMPLE QUESTIONS** ("what is X?", "define X", "tell me in simple way", "simply", "just tell me"):
- MAXIMUM 2-3 sentences ONLY
- Give direct definition + one example
- DO NOT add sections, headers, or detailed explanations
- DO NOT use words like "comprehensive", "key components", "practical applications"
- Example: "What is a neuron?" → "A neuron is a nerve cell that transmits electrical signals in the brain. It receives signals through dendrites and sends them through axons to other neurons."

**EXPLANATION QUESTIONS** ("how does X work?", "explain X"):
- Keep to 4-5 sentences maximum
- Focus on core mechanism only
- No multiple sections or detailed breakdowns

**COMPLEX QUESTIONS** ("analyze", "detailed explanation", "comprehensive", "compare"):
- Only then provide detailed analysis with sections

**WARNING SIGNS TO AVOID:**
- Adding sections like "Key Components", "Practical Applications", "Summary" for simple questions
- Using phrases like "comprehensive explanation" for basic definitions
- Writing multiple paragraphs when user asks "simply" or "in simple way"

IF USER SAYS "SIMPLE", "SIMPLY", "JUST", "BRIEF" - KEEP IT UNDER 3 SENTENCES!

If the transcript lacks information, state this briefly and explain what IS covered.

STOP after answering the question. Do not expand further unless specifically requested.

YOUR ANSWER:"""


# Summary Prompt Template (for lecture overview)
SUMMARY_PROMPT_TEMPLATE = """You are an expert educational content analyst. Create a comprehensive summary that truly helps students understand the lecture content.

LECTURE TRANSCRIPT SECTIONS:
{context}

YOUR TASK:
Analyze the transcript and create a detailed, educational summary that captures the essence of what students need to learn.

REQUIRED STRUCTURE:

**Topic & Purpose** (2-3 sentences):
- What specific subject/problem is being addressed?
- What is the main learning objective or goal?
- Why is this topic important or relevant?

**Core Concepts & Mechanisms** (5-6 sentences):
- What are the key concepts, methods, or techniques explained?
- HOW do these concepts/methods work? (Step-by-step process)
- WHY do they work this way? (Underlying principles)
- What specific examples or applications are mentioned?
- How do the concepts connect to each other?

**Key Insights & Applications** (2-3 sentences):
- What are the most important takeaways for students?
- How is this knowledge applied in practice?
- What broader implications or connections are discussed?

QUALITY REQUIREMENTS:
✓ Each sentence must provide unique, valuable information
✓ Use SPECIFIC details, examples, and terminology from the transcript
✓ Explain the 'how' and 'why', not just 'what'
✓ Write in clear, educational language that builds understanding
✓ Focus on content that helps students learn, not just describe what was said
✓ Connect concepts logically to show relationships

AVOID:
❌ Generic phrases like "the video discusses" or "it explains"
❌ Repeating the same information in different words
❌ Vague statements without specific details
❌ Simply listing topics without explaining them

Write a comprehensive educational summary that teaches the key concepts effectively:

EDUCATIONAL SUMMARY:"""


# Keywords that trigger summary mode
SUMMARY_KEYWORDS = [
    "lecture about",
    "video about",
    "summary",
    "summarize",
    "overview",
    "explain this video",
    "explain this lecture",
    "main topic",
    "what is this",
    "what does this",
    "cover",
    "topics covered",
    "give me the summary",
    "give me summary",
    "can you summarize",
    "tell me about this",
    "what's this about",
    "lecture summary",
    "video summary",
    "content summary"
]


def detect_intent(question: str) -> str:
    """
    Detect if question is asking for summary or specific Q&A.
    
    Args:
        question: User's question
        
    Returns:
        "summary" or "qa"
    """
    question_lower = question.lower()
    
    for keyword in SUMMARY_KEYWORDS:
        if keyword in question_lower:
            return "summary"
    
    return "qa"


def create_qa_prompt() -> PromptTemplate:
    """Create prompt template for Q&A."""
    return PromptTemplate(
        template=QA_PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )


def create_summary_prompt() -> PromptTemplate:
    """Create prompt template for summary."""
    return PromptTemplate(
        template=SUMMARY_PROMPT_TEMPLATE,
        input_variables=["context"]
    )


def format_docs(docs: List) -> str:
    """
    Format retrieved documents into clean context string.
    Removes timestamps for better LLM synthesis.
    
    Args:
        docs: List of retrieved documents
        
    Returns:
        str: Formatted context without timestamps
    """
    formatted_parts = []
    
    for i, doc in enumerate(docs, 1):
        # Just use the text content, no timestamps
        text = doc.page_content.strip()
        formatted_parts.append(text)
    
    return "\n\n".join(formatted_parts)


def create_rag_chain(video_id: str):
    """
    Create RAG chain for specific Q&A.
    
    Args:
        video_id: Video ID to load vector store for
        
    Returns:
        Runnable chain for Q&A with retriever
    """
    print(f"🔗 Creating Q&A chain for video: {video_id}")
    
    # Load vector store
    vector_store = load_vector_store(video_id)
    if not vector_store:
        raise ValueError(f"Vector store not found for video: {video_id}")
    
    # Create retriever (gets top K chunks)
    retriever = create_retriever(vector_store)
    
    # Get LLM
    llm = get_llm()
    
    # Create prompt
    prompt = create_qa_prompt()
    
    # Create LCEL chain
    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print(f"✅ Q&A chain created")
    
    return rag_chain, retriever


def create_summary_chain(video_id: str):
    """
    Create summary chain for lecture overview.
    Gets more chunks for comprehensive summary.
    
    Args:
        video_id: Video ID to load vector store for
        
    Returns:
        Runnable chain for summarization
    """
    print(f"📚 Creating Summary chain for video: {video_id}")
    
    # Load vector store
    vector_store = load_vector_store(video_id)
    if not vector_store:
        raise ValueError(f"Vector store not found for video: {video_id}")
    
    # Get comprehensive content for summary - use multiple search strategies
    # 1. Get chunks from beginning (introduction/overview)
    intro_docs = vector_store.similarity_search("introduction concept explanation definition", k=8)
    
    # 2. Get main content chunks
    main_docs = vector_store.similarity_search("key important main concept method technique", k=8)
    
    # 3. Get additional diverse content
    extra_docs = vector_store.similarity_search("example application implementation process", k=6)
    
    # Combine and deduplicate
    all_docs = intro_docs + main_docs + extra_docs
    # Remove duplicates based on content
    unique_docs = []
    seen_content = set()
    for doc in all_docs:
        content_key = doc.page_content[:100]  # First 100 chars as key
        if content_key not in seen_content:
            unique_docs.append(doc)
            seen_content.add(content_key)
    
    # Limit to top 15 diverse chunks
    all_docs = unique_docs[:15]
    
    print(f"📄 Retrieved {len(all_docs)} diverse chunks for comprehensive summary")
    
    # Get LLM
    llm = get_llm()
    
    # Create prompt
    prompt = create_summary_prompt()
    
    # Create LCEL chain
    summary_chain = (
        {
            "context": lambda _: format_docs(all_docs)
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print(f"✅ Summary chain created")
    
    return summary_chain, all_docs
    
    print(f"📄 Retrieved {len(all_docs)} chunks for summary")
    
    # Get LLM
    llm = get_llm()
    
    # Create prompt
    prompt = create_summary_prompt()
    
    # Create LCEL chain
    summary_chain = (
        {
            "context": lambda _: format_docs(all_docs)
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print(f"✅ Summary chain created")
    
    return summary_chain, all_docs


def ask_question(
    video_id: str,
    question: str
) -> Dict:
    """
    Ask a question about a video with intent-based routing and timestamp support.
    
    Args:
        video_id: Video ID
        question: User's question
        
    Returns:
        Dict with answer and sources
    """
    print(f"\n❓ Question: {question}")
    
    # Check for study commands first
    study_command = detect_study_command(question)
    if study_command:
        print(f"📚 Study command detected: {study_command}")
        return handle_study_command(video_id, study_command)
    
    # Check for timestamp in question
    from app.rag.retriever import extract_timestamp_from_query, retrieve_by_timestamp
    timestamp = extract_timestamp_from_query(question)
    
    # Load vector store
    vector_store = load_vector_store(video_id)
    if not vector_store:
        raise ValueError(f"Vector store not found for video: {video_id}")
    
    # Detect intent
    intent = detect_intent(question)
    print(f"🎯 Detected intent: {intent}")
    
    if timestamp:
        # Timestamp-based retrieval
        print(f"🕐 Timestamp detected: {timestamp}")
        source_docs = retrieve_by_timestamp(vector_store, timestamp, k=5)
        
        # Create Q&A chain
        llm = get_llm()
        prompt = create_qa_prompt()
        
        chain = (
            {
                "context": lambda _: format_docs(source_docs),
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        answer = chain.invoke(question)
        
    elif intent == "summary":
        # Summary mode - use all chunks
        chain, source_docs = create_summary_chain(video_id)
        answer = chain.invoke({})
        
    else:
        # Q&A mode - use retriever
        chain, retriever = create_rag_chain(video_id)
        answer = chain.invoke(question)
        
        # Get source documents
        source_docs = retriever.invoke(question)
    
    # Format response
    response = {
        "answer": answer,
        "sources": [],
        "mode": "timestamp" if timestamp else intent
    }
    
    # Add source information with timestamps
    for doc in source_docs[:10]:  # Limit to 10 sources in response
        source = {
            "text": doc.page_content,
            "timestamp": doc.metadata.get("timestamp", "N/A"),
            "url": doc.metadata.get("url", ""),
            "start": doc.metadata.get("start", 0)
        }
        response["sources"].append(source)
    
    return response


def detect_study_command(question: str) -> str:
    """
    Detect if question is a study material command.
    
    Args:
        question: User's question/command
        
    Returns:
        "notes", "mcqs", "flashcards", or None
    """
    question_lower = question.lower().strip()
    
    # Direct commands
    if question_lower.startswith("/"):
        command = question_lower[1:]  # Remove /
        if command in ["notes", "note"]:
            return "notes"
        elif command in ["mcqs", "mcq", "quiz", "questions"]:
            return "mcqs"
        elif command in ["flashcards", "flashcard", "cards"]:
            return "flashcards"
    
    # Natural language detection
    study_commands = {
        "notes": ["make notes", "create notes", "generate notes", "give me notes", "show notes", "provide notes", "notes for", "notes on"],
        "mcqs": ["make quiz", "create mcq", "generate questions", "give me quiz", "mcq", "multiple choice", "mcqs", "quiz questions", "questions with options", "10 mcqs", "5 mcqs", "quiz question"],
        "flashcards": ["make flashcards", "create flashcards", "generate cards", "give me flashcards", "flash cards"]
    }
    
    # Check each command pattern
    for command, keywords in study_commands.items():
        for keyword in keywords:
            if keyword in question_lower:
                print(f"🔍 Study command detected: '{command}' (matched: '{keyword}')")
                return command
    
    print(f"❌ No study command detected in: '{question_lower}'")
    
    return None


def handle_study_command(video_id: str, command: str) -> Dict:
    """
    Handle study material generation commands.
    
    Args:
        video_id: Video ID
        command: Study command type
        
    Returns:
        Dict with study materials
    """
    try:
        from app.services.study_material_generator import (
            generate_detailed_notes_text,
            generate_mcqs_with_options
        )
        
        print(f"📚 Handling study command: {command} for video {video_id}")

        def get_full_transcript_text() -> str:
            try:
                from app.services.youtube_loader import load_youtube_transcript
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                transcript_data = load_youtube_transcript(video_url)
                transcript_text = transcript_data.get("full_text", "")
                if transcript_text:
                    print(f"📄 Loaded full transcript from YouTube: {len(transcript_text)} characters")
                    return transcript_text
            except Exception as youtube_error:
                print(f"⚠️ YouTube transcript reload failed, falling back to vector store: {youtube_error}")

            try:
                from app.rag.vector_store import load_vector_store
                vector_store = load_vector_store(video_id)
                if not vector_store:
                    return ""

                all_docs = vector_store.similarity_search("main concepts explanation examples", k=120)
                transcript_text = "\n".join([doc.page_content for doc in all_docs])
                print(f"📄 Loaded transcript from vector store fallback: {len(transcript_text)} characters")
                return transcript_text
            except Exception as vector_error:
                print(f"❌ Vector store transcript fallback failed: {vector_error}")
                return ""

        transcript_text = get_full_transcript_text()
        if not transcript_text:
            return {
                "answer": "⚠️ Could not load transcript for this video. Please re-ingest the video and try again.",
                "type": "error"
            }
        
        if command == "notes":
            print(f"📖 Generating detailed notes for {video_id}...")
            notes_text = generate_detailed_notes_text(transcript_text, video_id)

            return {
                "answer": notes_text,
                "type": "notes"
            }
            
        elif command == "mcqs":
            print(f"📋 Generating MCQs with options for {video_id}...")
            mcqs = generate_mcqs_with_options(transcript_text, video_id)
            
            # Format MCQ response with options
            mcq_text = "# ❓ Quiz Questions\n\n"
            
            if not mcqs:
                mcq_text += "⚠️ Could not generate MCQs. Try asking specific questions about the video content.\n"
            else:
                for i, mcq in enumerate(mcqs[:5], 1):
                    mcq_text += f"**Q{i}.** {mcq.get('question', 'N/A')}\n\n"
                    
                    options = mcq.get('options', [])
                    for j, option in enumerate(options, 1):
                        letter = chr(ord('A') + j - 1)  # A, B, C, D
                        mcq_text += f"   {letter}. {option}\n"
                    
                    correct_idx = mcq.get('correct_answer', -1)
                    if 0 <= correct_idx < len(options):
                        correct_letter = chr(ord('A') + correct_idx)
                        mcq_text += f"\n   ✅ **Correct Answer:** {correct_letter}\n"
                    
                    explanation = mcq.get('explanation', '')
                    if explanation:
                        mcq_text += f"   💡 **Explanation:** {explanation}\n"
                    
                    mcq_text += "\n---\n\n"
            
            return {
                "answer": mcq_text,
                "type": "mcqs",
                "materials": {"mcqs": mcqs}
            }

        elif command == "flashcards":
            return {
                "answer": "ℹ️ Flashcards button removed for now. Use /mcqs or /notes.",
                "type": "info"
            }
        
        else:
            # Default response for unknown commands
            return {
                "answer": f"Unknown study command: {command}",
                "type": "error"
            }
        
    except Exception as e:
        print(f"❌ Study command error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "answer": f"❌ Error generating {command}. Please try again.",
            "type": "error"
        }