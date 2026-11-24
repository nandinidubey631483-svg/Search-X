# ==============================================================================
# SearchX Backend Multi-Stage Dockerfile
# Stage 1: Compiles C++ Inverted Index & BM25 Core Retrieval Engine with CMake & GCC
# Stage 2: Python 3.12 Runtime with FastAPI, Uvicorn, and C++ CLI bridge
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: C++ Core Engine Builder
# ------------------------------------------------------------------------------
FROM debian:bookworm-slim AS cxx-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY core-engine/ ./core-engine/

WORKDIR /build/core-engine/build
RUN cmake .. -DCMAKE_BUILD_TYPE=Release && \
    cmake --build . --config Release --target searchx_engine test_document test_inverted_index test_ranking test_persistence && \
    ctest --output-on-failure

# ------------------------------------------------------------------------------
# Stage 2: Production Python Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Install system runtime dependencies and ensure python/python3 symlinks exist across all bin paths
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/local/bin/python3 /usr/bin/python && \
    ln -sf /usr/local/bin/python3 /usr/bin/python3 && \
    ln -sf /usr/local/bin/python3 /usr/local/bin/python

# Install Python application dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt && \
    ln -sf /usr/local/bin/uvicorn /usr/bin/uvicorn

# Copy compiled C++ binary from builder stage
COPY --from=cxx-builder /build/core-engine/build/searchx_engine /app/core-engine/build/searchx_engine

# Copy application source code
COPY backend/ /app/backend/
COPY crawler/ /app/crawler/
COPY scripts/ /app/scripts/

# Ensure scripts and C++ engine binary are executable, create application data directory, and setup non-root user
RUN chmod +x /app/core-engine/build/searchx_engine /app/scripts/*.py && \
    useradd -m -u 1000 searchx && \
    mkdir -p /data && \
    chown -R searchx:searchx /app /data

USER searchx

ENV PATH="/usr/local/bin:/usr/bin:$PATH"
ENV PYTHONPATH=/app
ENV SEARCHX_ENGINE_BIN=/app/core-engine/build/searchx_engine
ENV SEARCHX_INDEX_PATH=/data/searchx_index.bin
ENV DATABASE_URL=sqlite:////data/searchx.db
ENV REDIS_URL=redis://redis:6379/0

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["sh", "-c", "python3 scripts/seed_corpus.py && python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
