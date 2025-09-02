# Build stage - build the wheel using uv
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Build the wheel
RUN uv build --wheel --out-dir /dist

# Runtime stage - use uv base image
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy the wheel from builder
COPY --from=builder /dist/*.whl /tmp/

# Install the wheel and its dependencies
RUN uv venv && \
    uv pip install --no-cache /tmp/*.whl && \
    rm -rf /tmp/*.whl

# Environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the operator via the installed console script
CMD ["vcluster-argocd-enroller"]
