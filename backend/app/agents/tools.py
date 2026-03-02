"""
Tools for the learning agent.
Defines capabilities the agent can use.
"""

from langchain.tools import Tool
from typing import List
from app.rag.pipeline import ask_question as rag_ask_question


def create_retriever_tool(video_id: str) -> Tool:
    """
    Create a retriever tool for the agent.
    
    Args:
        video_id: Video ID to query
        
    Returns:
        Tool instance
    """
    def retriever_func(question: str) -> str:
        """Query the video transcript."""
        try:
            result = rag_ask_question(video_id, question)
            return result["answer"]
        except Exception as e:
            return f"Error retrieving information: {str(e)}"
    
    tool = Tool(
        name="VideoTranscriptRetriever",
        func=retriever_func,
        description="""
        Use this tool to answer questions about the YouTube video.
        Input should be a clear question about the video content.
        This tool searches the video transcript and provides accurate answers with timestamps.
        """
    )
    
    return tool


def create_summarizer_tool(video_id: str) -> Tool:
    """
    Create a summarizer tool for the agent.
    
    Args:
        video_id: Video ID to summarize
        
    Returns:
        Tool instance
    """
    def summarizer_func(query: str) -> str:
        """Summarize the video."""
        try:
            # Use summary mode
            result = rag_ask_question(video_id, "What is this lecture about?")
            return result["answer"]
        except Exception as e:
            return f"Error summarizing video: {str(e)}"
    
    tool = Tool(
        name="VideoSummarizer",
        func=summarizer_func,
        description="""
        Use this tool to get an overview or summary of the entire video.
        Input can be any request for summary, overview, or main topics.
        This tool provides a comprehensive summary of the video content.
        """
    )
    
    return tool


def create_agent_tools(video_id: str) -> List[Tool]:
    """
    Create all tools for the agent.
    
    Args:
        video_id: Video ID
        
    Returns:
        List of Tool instances
    """
    tools = [
        create_retriever_tool(video_id),
        create_summarizer_tool(video_id)
    ]
    
    return tools


# Test function
def test_tools():
    """Test tools functionality."""
    from app.services.youtube_loader import load_youtube_transcript
    from app.rag.splitter import split_transcript
    from app.rag.vector_store import create_vector_store, save_vector_store
    
    print("\n" + "="*60)
    print("Testing Agent Tools")
    print("="*60)
    
    try:
        # Prepare test data
        video_url = "https://www.youtube.com/watch?v=aircAruvnKk"
        print(f"\n📹 Loading video: {video_url}")
        
        transcript_data = load_youtube_transcript(video_url)
        video_id = transcript_data['video_id']
        
        chunks = split_transcript(transcript_data)
        test_chunks = chunks[:50]
        
        vector_store = create_vector_store(test_chunks, video_id)
        save_vector_store(vector_store, video_id)
        
        # Create tools
        print("\n🔧 Creating tools...")
        tools = create_agent_tools(video_id)
        
        print(f"✅ Created {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:50]}...")
        
        # Test retriever tool
        print("\n🧪 Testing VideoTranscriptRetriever...")
        retriever_tool = tools[0]
        result = retriever_tool.run("What is a neural network?")
        print(f"Result: {result[:200]}...")
        
        # Test summarizer tool
        print("\n🧪 Testing VideoSummarizer...")
        summarizer_tool = tools[1]
        result = summarizer_tool.run("summarize")
        print(f"Result: {result[:200]}...")
        
        print("\n✅ Tools test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Tools test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_tools()
