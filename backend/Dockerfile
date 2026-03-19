FROM python:3.13-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

EXPOSE 8000

# Use $PORT env if set by Render, fallback to 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]