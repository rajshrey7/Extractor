FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.115.12 \
    uvicorn==0.34.3 \
    pydantic==2.10.1 \
    aiosqlite==0.20.0

# Copy application
COPY mock_mosip_server.py .

# Create data directory
RUN mkdir -p /app/data

EXPOSE 7000

# Run the server
CMD ["uvicorn", "mock_mosip_server:app", "--host", "0.0.0.0", "--port", "7000"]