
# BUILD STAGE - Heavy with compilers

FROM python:3.11 AS builder

WORKDIR /app

# Heavy build tools for compiling C extensions
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install and compile Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
# Now /root/.local contains compiled packages

# PRODUCTION STAGE - Lightweight runtime

FROM python:3.11-slim

WORKDIR /app

# Install ONLY runtime libraries (no compilers)
RUN apt-get update && apt-get install -y \
    libssl3 \
    libffi8 \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY the compiled packages (not the build tools)
COPY --from=builder /root/.local /root/.local

# Copy application code (compiled to .pyc if you want)
COPY --chown=appuser:appuser . .
RUN python -m compileall .  # Optional: pre-compile to .pyc

# Runtime only
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000
CMD ["gunicorn", "app:application"]