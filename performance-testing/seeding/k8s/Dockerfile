# Docker image for farmer-registry performance testing seeding
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seeding scripts
COPY common.py .
COPY config.py .
COPY db.py .
COPY id_scheme.py .
COPY run.py .
COPY search_anchors.py .
COPY seed_manifest.py .
COPY rebuild_indexes.py .
COPY reassign_search_anchors.py .
COPY generators/ ./generators/

ENV PYTHONUNBUFFERED=1

# Force rebuild by touching db.py
RUN touch db.py && stat db.py

# Add a build timestamp to force rebuild
RUN echo "Build timestamp: $(date)" > /build_info.txt

# Set default command
CMD ["python", "run.py", "--help"]