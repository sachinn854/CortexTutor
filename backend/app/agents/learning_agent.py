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
CONVERSATIONAL_PROMPT = """You are an expert AI tutor specializing in educational content analysis and student guidance.

CONVERSATION HISTORY:
{chat_history}

RELEVANT EDUCATIONAL CONTENT:
{context}

STUDENT'S QUESTION: {question}

Your Task:
Provide a comprehensive, educational response that helps the student understand the concept deeply.

Response Guidelines:

**For Summary Requests:**
- Identify the core topic and main learning objectives
- Explain key concepts with specific details from the content
- Show how concepts connect and build upon each other
- Highlight practical applications and importance
- Structure: Main Topic (2 sentences) → Key Concepts (4-5 sentences) → Applications/Importance (2-3 sentences)

**CRITICAL - Response Length Matching:**

BEFORE ANSWERING, analyze what the student actually wants:

*Simple Questions* ("what is X?", "tell me in simple way", "define X", contains "simply", "just", "brief"):
- Give ONLY 2-3 sentences maximum
- Direct definition + brief example
- NO sections, NO headers, NO comprehensive explanations
- NO words like "comprehensive", "key components", "practical applications"
- Example format: "X is [definition]. It works by [basic mechanism]. For example, [simple example]."

*Explanation Questions* ("how does X work?", "why X?", "explain X" without "simple"):
- 4-6 sentences maximum
- Core concept + mechanism
- Keep focused on their specific question

*Complex Questions* ("analyze", "detailed", "comprehensive", "compare"):
- Only then use full paragraphs and sections
- Provide comprehensive analysis with examples

**ENFORCEMENT RULES:**
- If they say "simple", "simply", "just tell me", "brief" → MAXIMUM 3 sentences
- If they ask "what is" without complexity words → 2-3 sentences only
- Do NOT add sections like "Key Components", "Summary", "Applications" for simple questions
- STOP immediately after answering the basic question

Provide a response that matches the student's question complexity and intent.

**Timestamp Handling:**
- If the user mentions a timestamp (e.g., "at 2:51", "around 3:20"), locate and explain the concept discussed at that specific time
- Interpret timestamp references as requests to explain specific content from that moment
- Do not ask for clarification if the concept can be identified from the transcript
- Treat timestamps as direct references to video content at that time point

**Quality Standards:**
- Each sentence must add unique educational value
- Use specific details and examples from the transcript
- Explain mechanisms and reasoning, not just facts
- Build understanding progressively
- Write in clear, engaging educational language

**Length:**
- Simple definitions: 3-4 sentences
- Concept explanations: 1 paragraph (5-7 sentences)
- Summaries/Complex topics: 2-3 paragraphs
- Timestamp explanations: Focus on that specific moment's content

Provide a thorough, educational response that truly helps the student learn:

YOUR EDUCATIONAL RESPONSE:"""


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
        
        # Get chat history from messages
        messages = memory.messages
        history_text = ""
        
        if messages:
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
        memory.add_user_message(question)
        memory.add_ai_message(answer)
        
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
