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
QA_PROMPT_TEMPLATE = """You are a friendly AI tutor helping students learn from YouTube videos.

VIDEO TRANSCRIPT CONTEXT:
{context}

STUDENT'S QUESTION: {question}

INSTRUCTIONS:
- Answer in a clear, conversational, and helpful way
- Use ONLY information from the transcript above
- Explain concepts simply, as if talking to a friend
- If the transcript doesn't have enough info, say so honestly
- Keep your answer concise (2-3 paragraphs max)
- Don't mention timestamps in your answer (they're provided separately)

YOUR ANSWER:"""


# Summary Prompt Template (for lecture overview)
SUMMARY_PROMPT_TEMPLATE = """You are a friendly AI tutor helping students understand a YouTube video.

Read the transcript below and create a helpful summary.

FULL LECTURE TRANSCRIPT:
{context}

Please provide:
1. **Main Topic** (1-2 sentences): What is this video about?
2. **Key Concepts** (3-5 bullet points): What are the main ideas?
3. **What You'll Learn** (2-3 bullet points): Key takeaways for students

Keep it conversational and easy to understand!

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
    Format retrieved documents into context string.
    
    Args:
        docs: List of retrieved documents
        
    Returns:
        str: Formatted context with timestamps
    """
    formatted_parts = []
    
    for i, doc in enumerate(docs, 1):
        timestamp = doc.metadata.get('timestamp', 'N/A')
        text = doc.page_content
        formatted_parts.append(f"[{timestamp}] {text}")
    
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
    Gets ALL chunks from vector store.
    
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
    
    # Get ALL documents (not just top K)
    # Use a dummy query to get all docs
    all_docs = vector_store.similarity_search("", k=1000)
    
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
    Ask a question about a video with intent-based routing.
    
    Args:
        video_id: Video ID
        question: User's question
        
    Returns:
        Dict with answer and sources
    """
    print(f"\n❓ Question: {question}")
    
    # Detect intent
    intent = detect_intent(question)
    print(f"🎯 Detected intent: {intent}")
    
    if intent == "summary":
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
        "mode": intent  # Add mode to response
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
