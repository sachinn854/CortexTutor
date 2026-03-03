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

LENGTH CONTROL:
- For simple definition questions: 3-4 sentences only
- For explanatory questions: 1 short paragraph (4-6 sentences)
- For complex questions: 2 paragraphs maximum

QUALITY:
- Each sentence must add new information
- Explain HOW things work, not just WHAT they are
- Use specific details from the content
- End immediately after completing the explanation

If the transcript lacks information, state this briefly and explain what IS covered.

YOUR ANSWER:"""


# Summary Prompt Template (for lecture overview)
SUMMARY_PROMPT_TEMPLATE = """You are an expert content summarizer specializing in educational videos.

TRANSCRIPT SECTIONS:
{context}

TASK:
Analyze the transcript and create a clear, structured summary that explains the core concepts.

CRITICAL INSTRUCTIONS:
1. Each sentence must introduce a NEW meaningful point - avoid repetition
2. Focus on explaining HOW and WHY, not just WHAT
3. Connect ideas logically to show relationships between concepts
4. Use specific details from the content, not generic statements
5. Write exactly 8-10 distinct sentences, each adding unique value

STRUCTURE YOUR SUMMARY:

**Main Topic** (2 sentences):
- What specific problem or concept is being addressed?
- What is the core mechanism or idea being explained?

**Key Concepts** (4-5 sentences):
- How does the main mechanism work?
- What are the specific components or steps involved?
- Why is this approach effective or important?
- What makes this different from alternatives?

**Learning Outcomes** (2-3 sentences):
- What practical understanding does this provide?
- How does this connect to broader applications?

AVOID:
- Repeating the same idea in different words
- Generic phrases like "the video explains" or "it discusses"
- Vague statements without specific details
- Restating the topic multiple times

Write in clear, flowing language that teaches the concept effectively.

YOUR SUMMARY:"""


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
    "topics covered"
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
    
    # Get MORE documents for summary (top 15-20 chunks)
    # Use similarity search to get most representative content
    all_docs = vector_store.similarity_search("main topic key concepts overview", k=20)
    
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


# Test function
def test_rag_pipeline():
    """Test the complete RAG pipeline with both modes."""
    from app.services.youtube_loader import load_youtube_transcript
    from app.rag.splitter import split_transcript
    from app.rag.vector_store import create_vector_store, save_vector_store
    
    print("\n" + "="*60)
    print("Testing RAG Pipeline with Intent Routing")
    print("="*60)
    
    try:
        # Load and prepare data
        video_url = "https://www.youtube.com/watch?v=aircAruvnKk"
        print(f"\n📹 Loading video: {video_url}")
        
        transcript_data = load_youtube_transcript(video_url)
        video_id = transcript_data['video_id']
        
        # Split into chunks
        chunks = split_transcript(transcript_data)
        
        # Use first 100 chunks for testing
        test_chunks = chunks[:100]
        print(f"\nUsing {len(test_chunks)} chunks for testing")
        
        # Create and save vector store
        vector_store = create_vector_store(test_chunks, video_id)
        save_vector_store(vector_store, video_id)
        
        # Test questions
        test_questions = [
            "What is this lecture about?",  # Should trigger summary
            "What is a neural network?",     # Should trigger Q&A
            "Summarize this video",          # Should trigger summary
        ]
        
        for question in test_questions:
            print(f"\n" + "="*60)
            result = ask_question(video_id, question)
            
            print(f"\n🎯 Mode: {result['mode']}")
            print(f"\n💬 Answer:")
            print(result["answer"])
            
            print(f"\n📚 Sources ({len(result['sources'])} chunks):")
            for i, source in enumerate(result["sources"][:3], 1):
                print(f"\n  {i}. [{source['timestamp']}]")
                print(f"     {source['text'][:100]}...")
        
        print("\n" + "="*60)
        print("✅ RAG Pipeline test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ RAG Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_rag_pipeline()
