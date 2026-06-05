# Lightweight Alpine-based image for the MSX Flask Directory Server
# Use a small runtime base and keep build context minimal.

FROM python:3.12-alpine

# Set environment (avoid .pyc, ensure unbuffered logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Security: add non-root user
RUN addgroup -S app && adduser -S app -G app

WORKDIR /app

# Requirements first for layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and only the files needed for runtime.
COPY . ./

# Create an empty files directory for runtime mounts and set ownership.
RUN mkdir -p files && chown -R app:app files

USER app

EXPOSE 5001

# Healthcheck using standard Python library, no extra packages needed.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5001', timeout=3)" || exit 1

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "app:app"]
