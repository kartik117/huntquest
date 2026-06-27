FROM python:3.11-slim AS build
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

FROM python:3.11-slim
RUN useradd --system --no-create-home appuser
COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY src ./src
USER appuser
EXPOSE 8000
CMD ["uvicorn", "huntquest.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
