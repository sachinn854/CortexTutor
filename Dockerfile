FROM python:3.11-slim

WORKDIR /code

# Install dependencies first (layer cache)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Pre-download embedding model so first request isn't slow
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Pre-create runtime dirs
RUN mkdir -p ./backend/vector_db ./backend/study_materials

WORKDIR /code/backend

ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
