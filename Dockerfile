FROM python:3.11-slim

WORKDIR /app

COPY requirements-pipeline.txt .
RUN pip install --no-cache-dir -r requirements-pipeline.txt

COPY src/ src/
COPY scripts/ scripts/
COPY data/portfolio/ data/portfolio/
COPY data/signals/ data/signals/

CMD ["python", "scripts/run_pipeline.py", "--help"]
