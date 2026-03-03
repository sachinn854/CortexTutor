"""
LLM initialization and management.
Uses Groq API via OpenAI-compatible interface.
"""

from langchain_openai import ChatOpenAI
from typing import Optional
from .config import settings
import os


class LLMManager:
    """Manages LLM instance as a singleton."""
    
    _instance: Optional[ChatOpenAI] = None
    
    @classmethod
    def get_llm(cls):
        """Get or create LLM instance."""
        if cls._instance is None:
            cls._instance = cls._initialize_llm()
        return cls._instance
    
    @classmethod
    def _initialize_llm(cls):
        """Initialize Groq LLM via OpenAI interface."""
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        
        print(f"🤖 Initializing Groq: {settings.groq_model}")
        
        try:
            llm = ChatOpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1",
                model=settings.groq_model,
                temperature=0.7,
                max_tokens=512,
            )
            
            # Test connection
            print("🔍 Testing Groq connection...")
            test_response = llm.invoke("Hi")
            print(f"✅ Groq ready! Test: {test_response.content[:30]}...")
            
            return llm
            
        except Exception as e:
            print(f"❌ Groq connection failed: {str(e)}")
            print("\n📥 TROUBLESHOOTING:")
            print("1. Check GROQ_API_KEY in .env file")
            print("2. Get free API key: https://console.groq.com")
            print("3. Rate limit: 6000 tokens/min on free tier")
            raise
    
    @classmethod
    def reset(cls):
        """Reset LLM instance."""
        cls._instance = None


def get_llm():
    """Get the LLM instance."""
    return LLMManager.get_llm()
