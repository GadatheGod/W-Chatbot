FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y     gcc     g++     && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Install the package
RUN pip install -e .

# Create data directories
RUN mkdir -p /app/data/chroma /app/data/crawled /app/data/docs /app/data/conversations /app/data/logs

# Expose port
EXPOSE 13700

# Start the server
CMD ["python", "-m", "webaichat", "serve"]
