FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
COPY . /app
WORKDIR /app
RUN uv sync --no-dev --frozen
ENTRYPOINT ["uv", "run", "--no-dev", "cli_progress"]
