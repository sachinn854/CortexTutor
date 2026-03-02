"""
LLM initialization and management.
Uses Ollama for local LLM inference (FREE, no API limits).
"""

from langchain_community.llms import Ollama
from typing import Optional
from .config import settings


class LLMManager:
    """Manages LLM instance as a singleton."""
    
    _instance: Optional[Ollama] = None
    
    @classmethod
    def get_llm(cls):
        """Get or create LLM instance."""
        if cls._instance is None:
            cls._instance = cls._initialize_llm()
        return cls._instance
    
    @classmethod
    def _initialize_llm(cls):
        """Initialize Ollama LLM."""
        print(f"🤖 Initializing Ollama: {settings.ollama_model}")
        print(f"🔗 Ollama URL: {settings.ollama_base_url}")
        
        try:
            llm = Ollama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=0.7,
            )
            
            # Test connection
            print("🔍 Testing Ollama connection...")
            test_response = llm.invoke("Hi")
            print(f"✅ Ollama ready! Test: {test_response[:30]}...")
            
            return llm
            
        except Exception as e:
            print(f"❌ Ollama connection failed: {str(e)}")
            print("\n📥 TROUBLESHOOTING:")
            print("1. Check Ollama is running: Task Manager -> 'ollama'")
            print("2. Test: curl http://localhost:11434")
            print("3. Pull model: ollama pull llama3.2")
            raise
    
    @classmethod
    def reset(cls):
        """Reset LLM instance."""
        cls._instance = None


def get_llm():
    """Get the LLM instance."""
    return LLMManager.get_llm()
