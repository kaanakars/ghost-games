# The web app only. The analysis runs on a laptop; the app reads its saved results.
# Build for Azure (Intel/AMD servers), even from an Apple Silicon Mac:
#   docker buildx build --platform linux/amd64 -t ghost-games .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# requirements first, so Docker reuses this layer when only the code changes
COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app/ .

# don't run as root inside the container
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/_stcore/health')"

CMD ["streamlit", "run", "Home.py", "--server.port=8000", "--server.address=0.0.0.0"]
