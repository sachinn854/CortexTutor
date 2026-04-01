"""
Embeddings generation using HuggingFace models.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from typing import Optional
from app.core.config import settings


class EmbeddingsManager:
    """Manages embeddings model as a singleton."""
    
    _instance: Optional[HuggingFaceEmbeddings] = None
    
    @classmethod
    def get_embeddings(cls) -> HuggingFaceEmbeddings:
        """
        Get or create embeddings model instance.
        
        Returns:
            HuggingFaceEmbeddings: Initialized embeddings model
        """
        if cls._instance is None:
            cls._instance = cls._initialize_embeddings()
        return cls._instance
    
    @classmethod
    def _initialize_embeddings(cls) -> HuggingFaceEmbeddings:
        """Initialize the embeddings model."""
        print(f"🔍 Initializing embeddings: {settings.embedding_model}")
        
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={'device': 'cpu'},  # Use CPU for compatibility
                encode_kwargs={'normalize_embeddings': True}
            )
            
            print("✅ Embeddings initialized successfully")
            return embeddings
            
        except Exception as e:
            print(f"❌ Failed to initialize embeddings: {str(e)}")
            raise
    
    @classmethod
    def reset(cls):
        """Reset the embeddings instance (useful for testing)."""
        cls._instance = None


# Convenience function
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Get the application's embeddings model.
    
    Returns:
        HuggingFaceEmbeddings: Initialized embeddings model
        
    Example:
        >>> from app.rag.embeddings import get_embeddings
        >>> embeddings = get_embeddings()
        >>> vector = embeddings.embed_query("What is machine learning?")
    """
    return EmbeddingsManager.get_embeddings()


# Test function
def test_embeddings():
    """Test embeddings generation."""
    print("\n" + "="*60)
    print("Testing Embeddings")
    print("="*60)
    
    try:
        embeddings = get_embeddings()
        
        # Test with a simple query
        test_text = "What is machine learning?"
        print(f"\nGenerating embedding for: '{test_text}'")
        
        vector = embeddings.embed_query(test_text)
        
        print(f"✅ Embedding generated!")
        print(f"   Dimension: {len(vector)}")
        print(f"\n📊 Full vector (all {len(vector)} dimensions):")
        print(vector)
        print(f"\n   First 10 values: {vector[:10]}")
        print(f"   Last 10 values: {vector[-10:]}")
        
        # Test batch embedding
        test_texts = [
            "Neural networks are powerful",
            "Deep learning uses multiple layers",
            "AI is transforming technology"
        ]
        
        print(f"\nGenerating embeddings for {len(test_texts)} texts...")
        vectors = embeddings.embed_documents(test_texts)
        
        print(f"✅ Batch embeddings generated!")
        print(f"   Number of vectors: {len(vectors)}")
        print(f"   Dimension: {len(vectors[0])}")
        
        print("\n✅ Embeddings test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Embeddings test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_embeddings()
