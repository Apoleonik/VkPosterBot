FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1

ADD . /app
WORKDIR /app
RUN uv sync --frozen

CMD ["uv", "run", "main.py"]
