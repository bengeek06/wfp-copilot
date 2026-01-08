# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

###############################
# Builder stage (compile deps) #
###############################
FROM python:3.13.5-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies and upgrade system packages for security patches
RUN apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml .

# Create dummy package for installation
# This allows installing dependencies without copying the full source code,
# preserving the Docker cache for dependencies.
RUN mkdir app && touch app/__init__.py

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir .

###############################
# Development image           #
###############################
FROM builder AS development

# Build arguments for metadata
ARG BUILD_COMMIT=dev
ARG BUILD_DATE

# Copy application code
COPY . .

# Install dev dependencies from pyproject.toml
RUN pip install --no-cache-dir -e ".[dev]"

# Generate build metadata
RUN mkdir -p .meta && \
    echo "${BUILD_COMMIT}" > .meta/COMMIT && \
    echo "${BUILD_DATE:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}" > .meta/BUILD_DATE

# Set permissions for scripts
RUN chmod +x /app/wait-for-it.sh /app/docker-entrypoint.sh

# Environment variables
ENV FLASK_ENV=development \
    APP_MODE=development \
    RUN_MIGRATIONS=true

EXPOSE 5000
ENTRYPOINT ["/app/docker-entrypoint.sh"]

###############################
# Test stage                  #
###############################
FROM builder AS test

# Copy all application code including tests
COPY . .

# Install dev + test dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Generate build metadata
RUN mkdir -p .meta && \
    echo "${BUILD_COMMIT:-test}" > .meta/COMMIT && \
    echo "${BUILD_DATE:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}" > .meta/BUILD_DATE

# Test environment variables
ENV FLASK_ENV=testing \
    APP_MODE=testing \
    IN_DOCKER_CONTAINER=true \
    PYTEST_ADDOPTS="-v" \
    DATABASE_URL=sqlite:///:memory: \
    USE_GUARDIAN_SERVICE=False \
    USE_IDENTITY_SERVICE=False

CMD ["pytest"]

###############################
# Production runtime          #
###############################
FROM python:3.13.5-slim AS production

# Build arguments for metadata
ARG BUILD_COMMIT=unknown
ARG BUILD_DATE

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install runtime dependencies and upgrade system packages for security patches
RUN apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install gunicorn (before switching to non-root user)
RUN pip install --no-cache-dir gunicorn

# Copy only necessary application files
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY run.py wsgi.py VERSION .env.example ./
COPY wait-for-it.sh docker-entrypoint.sh ./

# Generate build metadata, set permissions and create non-root user
RUN mkdir -p .meta && \
    echo "${BUILD_COMMIT}" > .meta/COMMIT && \
    echo "${BUILD_DATE:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}" > .meta/BUILD_DATE && \
    chmod +x wait-for-it.sh docker-entrypoint.sh && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

ENV FLASK_ENV=production \
    APP_MODE=production \
    WAIT_FOR_DB=true \
    RUN_MIGRATIONS=true

EXPOSE 5000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
