# ai-nudge/backend/Dockerfile (Minimal for Docker Test)

# Use a lean Python 3.11 base image.
FROM python:3.11-slim-bookworm

# Set working directory inside the container.
WORKDIR /app/backend

# Copy *only* the minimal requirements for this test.
# FastAPI needs uvicorn, so ensure your requirements.txt only lists that for now, or just install them directly here.
# For simplicity in this test, let's install directly.
RUN pip install fastapi uvicorn

# Copy your minimal app code.
COPY api/main.py api/main.py

# Expose the port Uvicorn will run on.
EXPOSE 8000

# Command to run Uvicorn when container starts.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]