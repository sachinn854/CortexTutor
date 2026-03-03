# 🎓 YouTube Learning Assistant

An AI-powered learning assistant that helps you understand YouTube videos through intelligent Q&A. Built with RAG (Retrieval-Augmented Generation) architecture for accurate, context-aware responses.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![LangChain](https://img.shields.io/badge/LangChain-Latest-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🎯 Core Capabilities
- **Smart Q&A**: Ask questions about any YouTube video and get accurate answers
- **Timestamp Support**: Reference specific moments (e.g., "What was explained at 2:51?")
- **Conversation Memory**: Maintains context across multiple questions
- **Auto-Summarization**: Get comprehensive summaries of video content
- **Source Citations**: Every answer includes relevant timestamps

### 🧠 Advanced RAG Pipeline
- **Intelligent Chunking**: Optimized 800-char chunks with 150-char overlap
- **Semantic Search**: FAISS vector database with sentence-transformers embeddings
- **Hybrid Retrieval**: Combines semantic similarity + timestamp-based lookup
- **Intent Detection**: Automatically routes between Q&A, summary, and timestamp modes
- **Anti-Repetition**: Prompts engineered to avoid redundant responses

### 🎨 Modern UI/UX
- **ChatGPT-Style Interface**: Dark theme, smooth animations, professional design
- **Real-time Processing**: Live status updates during video ingestion
- **Embedded Player**: Watch video while asking questions
- **Responsive Design**: Works on desktop and mobile

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Groq API Key (free tier available)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd CortexTutor
```

2. **Set up Python environment**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

3. **Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

4. **Configure environment**
```bash
# Copy .env.example to .env
cp .env.example .env

# Add your Groq API key
GROQ_API_KEY=your_groq_api_key_here
```

Get your free Groq API key: https://console.groq.com

5. **Run the application**
```bash
# Start backend (from backend directory)
python -m uvicorn app.main:app --reload

# Access the app
# Open browser: http://localhost:8000
```

## 📖 Usage

### Basic Workflow

1. **Paste YouTube URL**
   - Open http://localhost:8000
   - Paste any YouTube video URL
   - Wait 30-60 seconds for processing

2. **Ask Questions**
   ```
   "What is this video about?"
   "Explain the concept at 2:51"
   "How does attention mechanism work?"
   "Summarize the main points"
   ```

3. **Get Answers**
   - Receive accurate, context-aware responses
   - See relevant timestamps
   - Continue conversation naturally

### Advanced Features

**Timestamp Queries**
```
"What was explained at 3:20?"
"I didn't understand the part at 5:00"
"Can you explain what happens around 2:51?"
```

**Summary Requests**
```
"Summarize this video"
"What are the main topics?"
"Give me an overview"
```

**Follow-up Questions**
```
"Can you explain more?"
"What did you mean by that?"
"How does that relate to what we discussed?"
```

## 🏗️ Architecture

### Tech Stack

**Backend**
- **FastAPI**: High-performance API framework
- **LangChain**: RAG orchestration and LLM integration
- **Groq**: Ultra-fast LLM inference (llama-3.1-8b-instant)
- **FAISS**: Vector similarity search
- **Sentence Transformers**: Text embeddings (all-MiniLM-L6-v2)

**Frontend**
- **Vanilla JavaScript**: No framework overhead
- **Modern CSS**: ChatGPT-inspired dark theme
- **Responsive Design**: Mobile-friendly interface

### RAG Pipeline

```
YouTube URL
    ↓
Transcript Extraction (youtube-transcript-api)
    ↓
Intelligent Chunking (800 chars, 150 overlap)
    ↓
Embedding Generation (sentence-transformers)
    ↓
Vector Storage (FAISS)
    ↓
Query Processing
    ├─ Timestamp Detection → Direct Lookup
    ├─ Summary Intent → Comprehensive Retrieval
    └─ Q&A Intent → Semantic Search (Top 5)
    ↓
Context Formatting (Clean, no timestamps)
    ↓
LLM Generation (Groq)
    ↓
Response with Sources
```

### Key Components

**Retrieval System** (`backend/app/rag/`)
- `pipeline.py`: Main RAG orchestration
- `retriever.py`: Hybrid retrieval (semantic + timestamp)
- `vector_store.py`: FAISS management
- `splitter.py`: Intelligent chunking

**Agent System** (`backend/app/agents/`)
- `learning_agent.py`: Conversational AI tutor
- `memory.py`: Chat history management
- `tools.py`: Utility functions

**API Layer** (`backend/app/api/`)
- `ingest.py`: Video processing endpoint
- `chat.py`: Q&A endpoint

## ⚙️ Configuration

### Environment Variables

```bash
# LLM Configuration
GROQ_API_KEY=your_groq_api_key

# Vector Database
VECTOR_DB_TYPE=faiss
VECTOR_DB_PATH=./vector_db

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

### RAG Settings (`backend/app/core/config.py`)

```python
# Chunking
chunk_size = 800          # Characters per chunk
chunk_overlap = 150       # Overlap between chunks

# Retrieval
retrieval_top_k = 5       # Number of chunks to retrieve

# Embeddings
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

# LLM
groq_model = "llama-3.1-8b-instant"
```

## 🎯 Prompt Engineering

Our prompts are optimized for:
- **Synthesis over extraction**: Explains concepts, doesn't just copy
- **Length control**: Adapts response length to question complexity
- **Anti-repetition**: Each sentence adds unique value
- **Timestamp awareness**: Handles time-based references intelligently

Example prompt structure:
```
INSTRUCTIONS:
- Answer directly, no introductions
- Simple questions: 3-4 sentences
- Explanatory questions: 1 paragraph
- Complex questions: 2 paragraphs max
- If timestamp mentioned, explain content at that time
```

## 📊 Performance

- **Processing Time**: 30-60 seconds per video
- **Query Response**: 2-3 seconds
- **Embedding Model**: 384 dimensions
- **Vector Search**: Sub-second retrieval
- **LLM Speed**: ~100 tokens/second (Groq)

## 🔧 Development

### Project Structure

```
CortexTutor/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agent logic
│   │   ├── api/             # FastAPI endpoints
│   │   ├── core/            # Config, LLM, middleware
│   │   ├── rag/             # RAG pipeline
│   │   ├── services/        # YouTube loader
│   │   └── main.py          # App entry point
│   ├── vector_db/           # FAISS indices
│   ├── study_materials/     # Generated summaries
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Main UI
│   ├── app.js              # Frontend logic
│   └── styles.css          # ChatGPT-style theme
└── README.md
```

### Running Tests

```bash
# Test RAG pipeline
python -m backend.app.rag.pipeline

# Test retriever
python -m backend.app.rag.retriever

# Test memory
python -m backend.app.agents.memory
```

### Adding New Features

1. **Custom Prompts**: Edit `backend/app/rag/pipeline.py`
2. **New Endpoints**: Add to `backend/app/api/endpoints/`
3. **UI Changes**: Modify `frontend/` files

## 🐛 Troubleshooting

### Common Issues

**"Vector store not found"**
- Make sure video is ingested first
- Check `backend/vector_db/{video_id}/` exists

**"Rate limit exceeded"**
- Groq free tier: 6000 tokens/min
- Wait a minute and retry
- Consider upgrading Groq plan

**"No transcript available"**
- Video must have captions/subtitles
- Try a different video
- Check video is public

**Frontend not loading**
- Ensure backend is running on port 8000
- Clear browser cache (Ctrl+F5)
- Check browser console for errors

## 🚀 Deployment

### Option 1: Single Server

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
export GROQ_API_KEY=your_key

# Run with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### Option 2: Docker (Coming Soon)

```bash
docker-compose up
```

## 📝 License

MIT License - feel free to use for personal or commercial projects

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 🙏 Acknowledgments

- **LangChain**: RAG framework
- **Groq**: Lightning-fast LLM inference
- **FAISS**: Efficient vector search
- **FastAPI**: Modern Python web framework

## 📧 Contact

For questions or feedback, open an issue on GitHub.

---

**Built with ❤️ for learners everywhere**

*Turn any YouTube video into an interactive learning experience* 🎓
