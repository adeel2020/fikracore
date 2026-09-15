FROM python:3.14-slim AS builder

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY shared ./shared
COPY services ./services

RUN uv sync \
    --frozen \
    --no-dev

RUN ls -la /build/shared
RUN uv pip install --no-deps --no-cache-dir ./shared/
RUN uv pip list --python /build/.venv/bin/python | grep agentic


# Cleanup unnecessary files from virtual environment
RUN find /build/.venv -type d -name "__pycache__" -prune -exec rm -rf {} + && \
    find /build/.venv -type f -name "*.pyc" -delete && \
    find /build/.venv -type d -name "*.egg-info" -prune -exec rm -rf {} + && \
    rm -rf /root/.cache

FROM python:3.14-slim

WORKDIR /app

RUN groupadd -r agent && \
    useradd -r -g agent -d /app -s /usr/sbin/nologin agent && \
    mkdir -p /app/home/.local/share && \
    chown -R agent:agent /app

COPY --chown=agent:agent --from=builder /build/.venv /app/.venv
COPY --chown=agent:agent services/agents/src ./src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    PORT=8001 \
    HOME=/app/home \
    XDG_DATA_HOME=/app/home/.local/share

USER agent

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]