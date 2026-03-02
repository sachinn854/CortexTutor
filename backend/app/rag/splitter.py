"""
Text splitter for breaking transcripts into chunks while preserving timestamps.
Uses lazy loading for memory efficiency.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Dict, Iterator
from app.core.config import settings


def split_transcript(
    transcript_data: Dict,
    chunk_size: int = None,
    chunk_overlap: int = None,
    lazy: bool = False
) -> List[Document]:
    """
    Split transcript into chunks while preserving timestamp metadata.
    
    Args:
        transcript_data: Dict from youtube_loader with 'transcript', 'video_id', etc.
        chunk_size: Size of each chunk (default from settings)
        chunk_overlap: Overlap between chunks (default from settings)
        lazy: If True, returns generator for memory efficiency
        
    Returns:
        List[Document] or Iterator[Document]: LangChain documents with text and metadata
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if chunk_overlap is None:
        chunk_overlap = settings.chunk_overlap
    
    print(f"📄 Splitting transcript into chunks...")
    print(f"   Chunk size: {chunk_size}, Overlap: {chunk_overlap}")
    print(f"   Lazy loading: {lazy}")
    
    # Create text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    if lazy:
        # Lazy loading - returns generator
        return _split_transcript_lazy(transcript_data, text_splitter)
    else:
        # Load all at once
        return _split_transcript_eager(transcript_data, text_splitter)


def _split_transcript_eager(
    transcript_data: Dict,
    text_splitter: RecursiveCharacterTextSplitter
) -> List[Document]:
    """Eager loading - loads everything into memory."""
    
    # Create documents from transcript segments
    documents = []
    
    for segment in transcript_data['transcript']:
        doc = Document(
            page_content=segment['text'],
            metadata={
                'video_id': transcript_data['video_id'],
                'video_url': transcript_data['video_url'],
                'start': segment['start'],
                'duration': segment['duration'],
                'timestamp': segment['timestamp'],
                'url': segment['url'],
                'source': 'youtube'
            }
        )
        documents.append(doc)
    
    print(f"✅ Created {len(documents)} initial documents")
    
    # Split documents into chunks
    split_docs = text_splitter.split_documents(documents)
    
    print(f"✅ Split into {len(split_docs)} chunks")
    
    return split_docs


def _split_transcript_lazy(
    transcript_data: Dict,
    text_splitter: RecursiveCharacterTextSplitter
) -> Iterator[Document]:
    """Lazy loading - yields documents one at a time."""
    
    print(f"✅ Using lazy loading (memory efficient)")
    
    # Process segments in batches
    batch_size = 10
    batch = []
    
    for segment in transcript_data['transcript']:
        doc = Document(
            page_content=segment['text'],
            metadata={
                'video_id': transcript_data['video_id'],
                'video_url': transcript_data['video_url'],
                'start': segment['start'],
                'duration': segment['duration'],
                'timestamp': segment['timestamp'],
                'url': segment['url'],
                'source': 'youtube'
            }
        )
        batch.append(doc)
        
        # Process batch when full
        if len(batch) >= batch_size:
            split_docs = text_splitter.split_documents(batch)
            for split_doc in split_docs:
                yield split_doc
            batch = []
    
    # Process remaining documents
    if batch:
        split_docs = text_splitter.split_documents(batch)
        for split_doc in split_docs:
            yield split_doc


def split_text_simple(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[str]:
    """
    Simple text splitting without metadata (for testing).
    
    Args:
        text: Text to split
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List[str]: Text chunks
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if chunk_overlap is None:
        chunk_overlap = settings.chunk_overlap
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    chunks = text_splitter.split_text(text)
    return chunks


# Test function
def test_splitter():
    """Test the text splitter."""
    from app.services.youtube_loader import load_youtube_transcript
    
    print("\n" + "="*60)
    print("Testing Text Splitter")
    print("="*60)
    
    # Load a sample video
    video_url = "https://www.youtube.com/watch?v=aircAruvnKk"
    transcript_data = load_youtube_transcript(video_url)
    
    # Split with default settings (eager loading)
    print("\n--- Testing Eager Loading ---")
    chunks = split_transcript(transcript_data, lazy=False)
    
    print(f"\nOriginal segments: {len(transcript_data['transcript'])}")
    print(f"After splitting: {len(chunks)} chunks")
    
    # Show first 3 chunks
    print("\nFirst 3 chunks:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i+1} ---")
        if i == 0:
            # Show full text for first chunk
            print(f"Full Text: {chunk.page_content}")
        else:
            # Show preview for others
            print(f"Text: {chunk.page_content[:100]}...")
        print(f"Timestamp: {chunk.metadata['timestamp']}")
        print(f"URL: {chunk.metadata['url']}")
    
    # Test lazy loading
    print("\n\n--- Testing Lazy Loading ---")
    lazy_chunks = split_transcript(transcript_data, lazy=True)
    
    # Process first 5 chunks from generator
    print("\nFirst 5 chunks (lazy):")
    for i, chunk in enumerate(lazy_chunks):
        if i >= 5:
            break
        print(f"{i+1}. [{chunk.metadata['timestamp']}] {chunk.page_content[:50]}...")
    
    print("\n✅ Splitter test passed!")
    return True


if __name__ == "__main__":
    test_splitter()
