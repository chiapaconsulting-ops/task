# Small official Python base: faster builds, smaller attack surface.
FROM python:3.12-slim

# All subsequent commands run from /app inside the container.
WORKDIR /app

# Copy dependency list first so pip layer caches unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY app/ ./app/

# Run as non-root.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8080

CMD ["python", "app/main.py"]
