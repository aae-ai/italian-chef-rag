FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Copy requirements first (for caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# IMPORTANT: app.py → app:app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
