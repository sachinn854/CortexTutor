"""
Vector store management using FAISS.
Stores and retrieves document embeddings.
"""

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List, Optional
import os
from app.rag.embeddings import get_embeddings
from app.core.config import settings


def create_vector_store(
    documents: List[Document],
    video_id: str = None
) -> FAISS:
    """
    Create a new FAISS vector store from documents.
    
    Args:
        documents: List of LangChain documents with embeddings
        video_id: Optional video ID for naming the store
        
    Returns:
        FAISS: Vector store instance
    """
    print(f"💾 Creating vector store...")
    print(f"   Documents: {len(documents)}")
    
    # Get embeddings model
    embeddings = get_embeddings()
    
    # Create FAISS vector store
    vector_store = FAISS.from_documents(
        documents=documents,
        embedding=embeddings
    )
    
    print(f"✅ Vector store created with {len(documents)} documents")
    
    return vector_store


def save_vector_store(
    vector_store: FAISS,
    video_id: str
) -> str:
    """
    Save vector store to disk.
    
    Args:
        vector_store: FAISS vector store instance
        video_id: Video ID for naming
        
    Returns:
        str: Path where store was saved
    """
    # Create directory if it doesn't exist
    os.makedirs(settings.vector_db_path, exist_ok=True)
    
    # Save path
    save_path = os.path.join(settings.vector_db_path, video_id)
    
    print(f"💾 Saving vector store to: {save_path}")
    
    # Save to disk
    vector_store.save_local(save_path)
    
    print(f"✅ Vector store saved successfully")
    
    return save_path


def load_vector_store(video_id: str) -> Optional[FAISS]:
    """
    Load vector store from disk.
    
    Args:
        video_id: Video ID to load
        
    Returns:
        FAISS: Loaded vector store or None if not found
    """
    load_path = os.path.join(settings.vector_db_path, video_id)
    
    if not os.path.exists(load_path):
        print(f"⚠️  Vector store not found: {load_path}")
        return None
    
    print(f"📂 Loading vector store from: {load_path}")
    
    # Get embeddings model
    embeddings = get_embeddings()
    
    # Load from disk
    vector_store = FAISS.load_local(
        load_path,
        embeddings,
        allow_dangerous_deserialization=True  # Required for FAISS
    )
    
    print(f"✅ Vector store loaded successfully")
    
    return vector_store


def add_documents_to_store(
    vector_store: FAISS,
    documents: List[Document]
) -> FAISS:
    """
    Add more documents to existing vector store.
    
    Args:
        vector_store: Existing FAISS vector store
        documents: New documents to add
        
    Returns:
        FAISS: Updated vector store
    """
    print(f"➕ Adding {len(documents)} documents to vector store...")
    
    vector_store.add_documents(documents)
    
    print(f"✅ Documents added successfully")
    
    return vector_store


# Test function
def test_vector_store():
    """Test vector store creation and retrieval."""
    from app.services.youtube_loader import load_youtube_transcript
    from app.rag.splitter import split_transcript
    
    print("\n" + "="*60)
    print("Testing Vector Store")
    print("="*60)
    
    try:
        # Load and split transcript
        video_url = "https://www.youtube.com/watch?v=aircAruvnKk"
        transcript_data = load_youtube_transcript(video_url)
        chunks = split_transcript(transcript_data)
        
        # Use only first 50 chunks for testing (faster)
        test_chunks = chunks[:50]
        print(f"\nUsing {len(test_chunks)} chunks for testing")
        
        # Create vector store
        vector_store = create_vector_store(test_chunks, transcript_data['video_id'])
        
        # Test similarity search
        query = "What is a neural network?"
        print(f"\n🔍 Searching for: '{query}'")
        
        results = vector_store.similarity_search(query, k=3)
        
        print(f"\n✅ Found {len(results)} relevant chunks:")
        for i, doc in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Text: {doc.page_content[:150]}...")
            print(f"Timestamp: {doc.metadata['timestamp']}")
            print(f"URL: {doc.metadata['url']}")
        
        # Test save and load
        print(f"\n💾 Testing save/load...")
        save_path = save_vector_store(vector_store, transcript_data['video_id'])
        
        loaded_store = load_vector_store(transcript_data['video_id'])
        
        if loaded_store:
            print(f"✅ Successfully loaded vector store")
            
            # Test search on loaded store
            results2 = loaded_store.similarity_search(query, k=1)
            print(f"✅ Search on loaded store works: {len(results2)} results")
        
        print("\n✅ Vector store test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Vector store test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_vector_store()
