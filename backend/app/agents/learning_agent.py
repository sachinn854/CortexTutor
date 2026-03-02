"""
Learning Agent - Intelligent orchestration with memory and tools.
Provides conversational AI tutor experience.
Simplified version without complex agent framework.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import Dict
from app.core.llm import get_llm
from app.agents.memory import create_memory
from app.rag.pipeline import ask_question as rag_ask_question


# Conversational Prompt Template
CONVERSATIONAL_PROMPT = """You are an AI tutor helping students learn from YouTube videos.

Previous conversation:
{chat_history}

Current question: {question}

Video context: {context}

Provide a helpful, educational answer that:
1. Uses ONLY information from the video context
2. References the conversation history if relevant
3. Includes timestamps when helpful
4. Is clear and easy to understand

Answer:"""


def chat_with_agent(
    video_id: str,
    question: str,
    session_id: str = "default"
) -> Dict:
    """
    Chat with conversational memory.
    
    Args:
        video_id: Video ID
        question: User's question
        session_id: Session ID for conversation history
        
    Returns:
        Dict with answer and metadata
    """
    print(f"\n💬 Chat with memory (session: {session_id})")
    print(f"❓ Question: {question}")
    
    try:
        # Get memory
        memory = create_memory(session_id)
        
        # Get answer from RAG
        rag_result = rag_ask_question(video_id, question)
        
        # Get chat history
        chat_history = memory.load_memory_variables({})
        history_text = ""
        
        if chat_history.get("chat_history"):
            messages = chat_history["chat_history"]
            history_text = "\n".join([
                f"{'Student' if msg.type == 'human' else 'Tutor'}: {msg.content}"
                for msg in messages[-4:]  # Last 4 messages
            ])
        
        # Create conversational prompt
        llm = get_llm()
        prompt = ChatPromptTemplate.from_template(CONVERSATIONAL_PROMPT)
        
        # Create chain
        chain = prompt | llm | StrOutputParser()
        
        # Get conversational answer
        answer = chain.invoke({
            "chat_history": history_text if history_text else "No previous conversation",
            "question": question,
            "context": "\n".join([
                f"[{s['timestamp']}] {s['text']}"
                for s in rag_result["sources"][:5]
            ])
        })
        
        # Save to memory
        memory.save_context(
            {"question": question},
            {"answer": answer}
        )
        
        response = {
            "answer": answer,
            "video_id": video_id,
            "session_id": session_id
        }
        
        print(f"✅ Conversational response generated")
        
        return response
        
    except Exception as e:
        print(f"❌ Agent error: {str(e)}")
        # Fallback to direct RAG
        result = rag_ask_question(video_id, question)
        
        return {
            "answer": result["answer"],
            "video_id": video_id,
            "session_id": session_id,
            "fallback": True
        }


# Test function
def test_learning_agent():
    """Test conversational memory."""
    from app.services.youtube_loader import load_youtube_transcript
    from app.rag.splitter import split_transcript
    from app.rag.vector_store import create_vector_store, save_vector_store
    
    print("\n" + "="*60)
    print("Testing Conversational Agent")
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
        
        # Test multi-turn conversation
        session_id = "test_conversation"
        
        questions = [
            "What is this video about?",
            "Can you explain more?",  # Tests memory
            "What did you just tell me?"  # Tests memory
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*60}")
            print(f"Turn {i}")
            print(f"{'='*60}")
            
            result = chat_with_agent(video_id, question, session_id)
            
            print(f"\n💬 Answer:")
            print(result["answer"][:300] + "...")
            
            if result.get("fallback"):
                print("\n⚠️  Used fallback")
        
        print("\n" + "="*60)
        print("✅ Conversational agent test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_learning_agent()
