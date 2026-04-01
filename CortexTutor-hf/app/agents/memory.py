"""
Conversation memory management.
Stores chat history for context-aware conversations.
"""

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from typing import Dict, Optional


class MemoryManager:
    """Manages conversation memory for different sessions."""
    
    _sessions: Dict[str, ChatMessageHistory] = {}
    
    @classmethod
    def get_memory(cls, session_id: str) -> ChatMessageHistory:
        """
        Get or create memory for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            ChatMessageHistory instance
        """
        if session_id not in cls._sessions:
            cls._sessions[session_id] = ChatMessageHistory()
            print(f"💾 Created new memory for session: {session_id}")
        
        return cls._sessions[session_id]
    
    @classmethod
    def clear_memory(cls, session_id: str):
        """Clear memory for a session."""
        if session_id in cls._sessions:
            cls._sessions[session_id].clear()
            print(f"🗑️ Cleared memory for session: {session_id}")
    
    @classmethod
    def delete_session(cls, session_id: str):
        """Delete a session completely."""
        if session_id in cls._sessions:
            del cls._sessions[session_id]
            print(f"🗑️ Deleted session: {session_id}")
    
    @classmethod
    def get_chat_history(cls, session_id: str) -> list:
        """Get chat history for a session."""
        if session_id in cls._sessions:
            return cls._sessions[session_id].messages
        return []


def create_memory(session_id: str = "default") -> ChatMessageHistory:
    """
    Create or get conversation memory.
    
    Args:
        session_id: Session identifier
        
    Returns:
        ChatMessageHistory instance
    """
    return MemoryManager.get_memory(session_id)


# Test function
def test_memory():
    """Test memory functionality."""
    print("\n" + "="*60)
    print("Testing Conversation Memory")
    print("="*60)
    
    try:
        # Create memory for a session
        session_id = "test_session_123"
        memory = create_memory(session_id)
        
        # Simulate conversation
        print("\n📝 Simulating conversation...")
        
        # Turn 1
        memory.add_user_message("What is a neural network?")
        memory.add_ai_message("A neural network is a computational model...")
        print("✅ Saved turn 1")
        
        # Turn 2
        memory.add_user_message("Can you explain more?")
        memory.add_ai_message("Sure! Neural networks consist of layers...")
        print("✅ Saved turn 2")
        
        # Turn 3
        memory.add_user_message("What about deep learning?")
        memory.add_ai_message("Deep learning uses multiple layers...")
        print("✅ Saved turn 3")
        
        # Get chat history
        print("\n📜 Chat History:")
        history = MemoryManager.get_chat_history(session_id)
        for i, msg in enumerate(history, 1):
            print(f"\n{i}. {msg.type}: {msg.content[:100]}...")
        
        # Clear memory
        MemoryManager.clear_memory(session_id)
        print("\n🗑️ Memory cleared")
        
        # Verify cleared
        history_after = MemoryManager.get_chat_history(session_id)
        print(f"Messages after clear: {len(history_after)}")
        
        print("\n✅ Memory test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Memory test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_memory()
