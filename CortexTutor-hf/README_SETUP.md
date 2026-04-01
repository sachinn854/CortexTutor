# 🚀 Phase 1 Setup Guide

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- HuggingFace account (free) - [Sign up here](https://huggingface.co/join)

---

## Step 1: Create Virtual Environment

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

---

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (web framework)
- LangChain (LLM orchestration)
- HuggingFace libraries (LLM & embeddings)
- ChromaDB (vector database)
- YouTube Transcript API
- Other utilities

---

## Step 3: Configure Environment Variables

1. Copy the example environment file:
```bash
copy .env.example .env
```

2. Get your HuggingFace API token:
   - Go to https://huggingface.co/settings/tokens
   - Click "New token"
   - Give it a name (e.g., "youtube-learning-assistant")
   - Copy the token

3. Edit `.env` file and add your token:
```env
HUGGINGFACE_API_TOKEN=hf_your_actual_token_here
```

---

## Step 4: Test the Setup

Run the test script to verify everything is working:

```bash
python test_setup.py
```

You should see:
- ✅ Imports test passed
- ✅ Configuration test passed
- ✅ LLM test passed (if token is configured)

---

## Step 5: Start the Server

```bash
# Option 1: Using Python directly
python -m app.main

# Option 2: Using Uvicorn
uvicorn app.main:app --reload
```

The server will start at: http://localhost:8000

---

## Step 6: Verify Server is Running

Open your browser and visit:

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

You should see the interactive API documentation (Swagger UI).

---

## 🎯 What We've Built (Phase 1)

✅ **Core Configuration** (`app/core/config.py`)
- Loads environment variables
- Manages all application settings
- Validates configuration on startup

✅ **LLM Manager** (`app/core/llm.py`)
- Initializes HuggingFace LLM
- Singleton pattern for efficiency
- Error handling and testing utilities

✅ **FastAPI Application** (`app/main.py`)
- Basic server setup
- CORS configuration
- Health check endpoints
- Ready for API routes

✅ **Dependencies** (`requirements.txt`)
- All required packages
- Version pinned for stability

---

## 🔧 Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution**: Make sure virtual environment is activated and dependencies are installed
```bash
pip install -r requirements.txt
```

### Issue: "HuggingFace API token not found"
**Solution**: Check your `.env` file has the correct token
```bash
# Verify .env file exists
dir .env

# Check token is set (don't share the output!)
type .env
```

### Issue: "Port 8000 already in use"
**Solution**: Change port in `.env` file
```env
PORT=8001
```

### Issue: LLM test fails with timeout
**Solution**: 
- Check internet connection
- Try a different model in `.env`:
```env
HUGGINGFACE_MODEL=google/flan-t5-small
```

---

## 📚 Configuration Options

You can customize these in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `HUGGINGFACE_API_TOKEN` | - | Your HF API token (required) |
| `HUGGINGFACE_MODEL` | `google/flan-t5-base` | LLM model to use |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `VECTOR_DB_TYPE` | `chroma` | Vector database type |
| `CHUNK_SIZE` | `1000` | Text chunk size |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `RETRIEVAL_TOP_K` | `4` | Number of chunks to retrieve |
| `PORT` | `8000` | Server port |
| `DEBUG` | `False` | Debug mode |

---

## 🎉 Success Criteria

Phase 1 is complete when:

- ✅ Virtual environment is created and activated
- ✅ All dependencies are installed
- ✅ `.env` file is configured with HuggingFace token
- ✅ `test_setup.py` passes all tests
- ✅ Server starts without errors
- ✅ You can access http://localhost:8000/docs

---

## 🚀 Next Steps

Once Phase 1 is complete, we'll move to:

**Phase 2: Services Layer**
- YouTube transcript loader (with timestamps!)
- Video metadata extraction

**Phase 3: RAG Layer**
- Text splitting
- Embeddings generation
- Vector store setup
- Retrieval pipeline

Ready to continue? Let's build the YouTube loader next! 🎬
