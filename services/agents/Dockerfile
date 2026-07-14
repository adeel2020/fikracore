FROM python:3.11-slim AS builder
WORKDIR /build
COPY shared/ ./shared/
COPY services/agents/ ./agents/
RUN pip install ./shared/

FROM python:3.11-slim
RUN groupadd -r agent && useradd -r -g agent -d /app -s /sbin/nologin agent
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY services/agents/src/ ./src/
COPY services/agents/pyproject.toml .
ENV PYTHONPATH=/app/src:$PYTHONPATH
ENV PORT=8001
USER agent
EXPOSE 8001
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
