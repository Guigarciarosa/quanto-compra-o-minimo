FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY data/snapshots ./data/snapshots
COPY docs ./docs
COPY eval ./eval
ENV PYTHONPATH=/app/src QCM_DB=/data/qcm.duckdb
CMD ["sh", "-c", "python -m qcm all && QCM_MCP_TRANSPORT=streamable-http qcm-mcp"]
