# Use Python 3.10 slim image for better security and smaller size
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p /home/appuser/.kaggle && \
    chown -R appuser:appuser /home/appuser && \
    chmod -R 755 /home/appuser

# Copy the rest of the application
COPY --chown=appuser:appuser . .

# Create entrypoint script that handles initialization properly
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Setting up Kaggle credentials..."\n\
if [ -n "$KAGGLE_USERNAME" ] && [ -n "$KAGGLE_API_KEY" ]; then\n\
    echo "{\"username\":\"$KAGGLE_USERNAME\",\"key\":\"$KAGGLE_API_KEY\"}" > /home/appuser/.kaggle/kaggle.json\n\
    chmod 600 /home/appuser/.kaggle/kaggle.json\n\
    echo "Kaggle credentials configured"\n\
fi\n\
\n\
# Function to wait for service with more robust checking\n\
wait_for_service() {\n\
    local service=$1\n\
    local host=$2\n\
    local port=$3\n\
    local health_path=$4\n\
    local max_attempts=60\n\
    local attempt=1\n\
    \n\
    echo "Waiting for $service to be ready..."\n\
    while [ $attempt -le $max_attempts ]; do\n\
        if nc -z $host $port 2>/dev/null; then\n\
            if curl -f http://$host:$port$health_path >/dev/null 2>&1; then\n\
                echo "$service is ready!"\n\
                return 0\n\
            fi\n\
        fi\n\
        echo "Attempt $attempt/$max_attempts: $service not ready yet, waiting..."\n\
        sleep 5\n\
        attempt=$((attempt + 1))\n\
    done\n\
    \n\
    echo "Warning: $service did not become ready within expected time"\n\
    return 1\n\
}\n\
\n\
echo "Waiting for dependencies to be ready..."\n\
wait_for_service "MLflow" "mlflow" "5000" "/health"\n\
wait_for_service "Prefect" "prefect" "4200" "/api/ready"\n\
\n\
# Additional wait to ensure services are fully initialized\n\
echo "Giving services additional time to fully initialize..."\n\
sleep 10\n\
\n\
# Check if pipeline should be run (optional - can be controlled via env var)\n\
if [ "${RUN_PIPELINE:-false}" = "true" ]; then\n\
    echo "Running pipeline..."\n\
    # Set timeout for pipeline execution\n\
    timeout 300 python -m src.pipelines.pipeline || {\n\
        echo "Pipeline execution failed or timed out, but continuing to start application..."\n\
    }\n\
else\n\
    echo "Skipping pipeline execution (RUN_PIPELINE not set to true)"\n\
fi\n\
\n\
echo "Starting application..."\n\
exec "$@"' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Change ownership of the entire app directory to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 7860

# Add health check endpoint (liveness: process is up)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Command to run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]