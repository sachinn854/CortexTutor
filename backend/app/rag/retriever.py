"""
Retriever for searching relevant document chunks.
Supports both semantic search and timestamp-based retrieval.
"""

from langchain_community.vectorstores import FAISS
from langchain_core.retrievers import BaseRetriever
from typing import List
import re
from app.core.config import settings


def extract_timestamp_from_query(query: str) -> str:
    """
    Extract timestamp from user query.
    
    Args:
        query: User's question
        
    Returns:
        Timestamp string (e.g., "02:51") or None
    """
    # Match patterns like: 2:51, 02:51, 3:20, etc.
    patterns = [
        r'\b(\d{1,2}):(\d{2})\b',  # 2:51 or 02:51
        r'\b(\d{1,2})\.(\d{2})\b',  # 2.51
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            # Normalize to MM:SS format
            return f"{minutes:02d}:{seconds:02d}"
    
    return None


def retrieve_by_timestamp(
    vector_store: FAISS,
    timestamp: str,
    k: int = 3
) -> List:
    """
    Retrieve documents near a specific timestamp.
    
    Args:
        vector_store: FAISS vector store
        timestamp: Target timestamp (e.g., "02:51")
        k: Number of documents to retrieve
        
    Returns:
        List of documents near the timestamp
    """
    print(f"🕐 Retrieving content near timestamp: {timestamp}")
    
    # Get all documents
    all_docs = vector_store.similarity_search("", k=1000)
    
    # Filter documents by timestamp proximity
    target_minutes, target_seconds = map(int, timestamp.split(':'))
    target_total_seconds = target_minutes * 60 + target_seconds
    
    docs_with_distance = []
    for doc in all_docs:
        doc_timestamp = doc.metadata.get('timestamp', '00:00')
        try:
            doc_minutes, doc_seconds = map(int, doc_timestamp.split(':'))
            doc_total_seconds = doc_minutes * 60 + doc_seconds
            
            # Calculate time distance
            distance = abs(doc_total_seconds - target_total_seconds)
            docs_with_distance.append((doc, distance))
        except:
            continue
    
    # Sort by distance and get top k
    docs_with_distance.sort(key=lambda x: x[1])
    nearest_docs = [doc for doc, _ in docs_with_distance[:k]]
    
    print(f"✅ Found {len(nearest_docs)} documents near {timestamp}")
    
    return nearest_docs


def create_retriever(
    vector_store: FAISS,
    search_type: str = "similarity",
    k: int = None
) -> BaseRetriever:
    """
    Create a retriever from vector store.
    
    Args:
        vector_store: FAISS vector store instance
        search_type: Type of search ("similarity" or "mmr")
        k: Number of documents to retrieve (default from settings)
        
    Returns:
        BaseRetriever: Configured retriever
    """
    if k is None:
        k = settings.retrieval_top_k
    
    print(f"🔍 Creating retriever...")
    print(f"   Search type: {search_type}")
    print(f"   Top K: {k}")
    
    retriever = vector_store.as_retriever(
        search_type=search_type,
        search_kwargs={"k": k}
    )
    
    print(f"✅ Retriever created successfully")
    
    return retriever


def retrieve_with_scores(
    vector_store: FAISS,
    query: str,
    k: int = None
) -> List[tuple]:
    """
    Retrieve documents with similarity scores.
    
    Args:
        vector_store: FAISS vector store
        query: Search query
        k: Number of results
        
    Returns:
        List[tuple]: List of (Document, score) tuples
    """
    if k is None:
        k = settings.retrieval_top_k
    
    results = vector_store.similarity_search_with_score(query, k=k)
    
    return results


# Test function
def test_retriever():
    """Test retriever functionality."""
    from app.services.youtube_loader import load_youtube_transcript
    from app.rag.splitter import split_transcript
    from app.rag.vector_store import create_vector_store
    
    print("\n" + "="*60)
    print("Testing Retriever")
    print("="*60)
    
    try:
        # Load and prepare data
        video_url = "https://www.youtube.com/watch?v=aircAruvnKk"
        transcript_data = load_youtube_transcript(video_url)
        chunks = split_transcript(transcript_data)
        
        # Use first 50 chunks for testing
        test_chunks = chunks[:50]
        print(f"\nUsing {len(test_chunks)} chunks for testing")
        
        # Create vector store
        vector_store = create_vector_store(test_chunks, transcript_data['video_id'])
        
        # Create retriever
        retriever = create_retriever(vector_store, k=3)
        
        # Test retrieval
        query = "How do neural networks learn?"
        print(f"\n🔍 Query: '{query}'")
        
        docs = retriever.invoke(query)
        
        print(f"\n✅ Retrieved {len(docs)} documents:")
        for i, doc in enumerate(docs, 1):
            print(f"\n--- Document {i} ---")
            print(f"Text: {doc.page_content[:100]}...")
            print(f"Timestamp: {doc.metadata['timestamp']}")
            print(f"URL: {doc.metadata['url']}")
        
        # Test with scores
        print(f"\n🔍 Testing retrieval with scores...")
        results_with_scores = retrieve_with_scores(vector_store, query, k=3)
        
        print(f"\n✅ Retrieved {len(results_with_scores)} documents with scores:")
        for i, (doc, score) in enumerate(results_with_scores, 1):
            print(f"\n--- Document {i} (Score: {score:.4f}) ---")
            print(f"Text: {doc.page_content[:100]}...")
            print(f"Timestamp: {doc.metadata['timestamp']}")
        
        print("\n✅ Retriever test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Retriever test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_retriever()
