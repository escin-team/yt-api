FROM python:3.12-slim

# 1. Buat user non-root
RUN useradd -m -u 1000 user

# 2. Set workdir
WORKDIR /app

# 3. Berikan kepemilikan folder /app ke user
RUN chown -R user:user /app

# 4. Install system dependencies sebagai root
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    git \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 5. Switch ke user biasa
USER user

# 6. Set PATH untuk uv dan bun
ENV PATH="/home/user/.local/bin:/home/user/.bun/bin:$PATH"

# 7. Install Bun
RUN curl -fsSL https://bun.sh/install | bash

# 8. Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# 9. Copy file yang dibutuhkan untuk build paket
COPY --chown=user pyproject.toml uv.lock README.md ./

# 10. Copy ISI folder src/ langsung ke /app/
COPY --chown=user src/youtube_search/ ./youtube_search/

# 11. Install Python dependencies
RUN uv sync --frozen --no-dev

# 12. Copy main.py
COPY --chown=user main.py ./

# 13. Buat direktori sementara
RUN mkdir -p /tmp/youtube_audio logs

# 14. HF Spaces WAJIB port 7860
EXPOSE 7860

# 15. Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# 16. Run application
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]