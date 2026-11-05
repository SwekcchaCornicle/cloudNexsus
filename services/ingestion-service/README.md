# CloudNexus — Ingestion Service (MVP)

A locally runnable FastAPI ingestion service for HTML documentation from AWS, Microsoft Azure and Google Cloud.

## What it does

- Accepts an HTML file through a multipart API.
- Validates file type and maximum size.
- Extracts title, headings, paragraphs, lists and code blocks.
- Removes navigation, scripts, styles, forms, headers and footers.
- Splits content into overlapping chunks.
- Stores normalized JSON artifacts and metadata locally.
- Includes unit tests and Docker support.

This is the first vertical slice. Local storage is used initially; the processing pipeline is designed so S3 and SQS adapters can be added without changing the parsing/chunking domain logic.

## Requirements

- Python 3.11+
- Docker (optional)

## Run locally (Windows CMD)

```cmd
cd cloudnexus-ingestion-starter
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open:
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## Ingest an HTML file

```cmd
curl -X POST "http://127.0.0.1:8000/api/v1/ingestion/jobs" ^
  -F "file=@fixtures/aws_lambda_sample.html" ^
  -F "provider=AWS" ^
  -F "service_name=Lambda" ^
  -F "source_url=https://docs.aws.amazon.com/lambda/latest/dg/welcome.html"
```

The response includes a `job_id`, `document_id`, chunk count and artifact path.

Artifacts are written under `data/processed/`. The original uploaded file is retained under `data/raw/`.

## Run tests

```cmd
pytest
```

## Run with Docker

```cmd
docker build -t cloudnexus-ingestion:local .
docker run --rm -p 8000:8000 -v "%cd%\data:/app/data" cloudnexus-ingestion:local
```

## API

`POST /api/v1/ingestion/jobs`

Multipart fields:
- `file`: HTML document
- `provider`: `AWS`, `AZURE` or `GCP`
- `service_name`: provider service name
- `source_url`: original official documentation URL

`GET /api/v1/ingestion/jobs/{job_id}` returns the processing result.

## Important MVP limitations

- Token counts are approximate whitespace-based counts, not model tokenizer counts.
- HTML parsing is best-effort; source-specific adapters and PDF support are future work.
- The local artifact store is for development only.
- This API accepts uploaded HTML. It does not crawl arbitrary URLs.
- Before collecting or redistributing provider documentation, review each provider's terms, robots policies, rate limits, attribution and reuse conditions.
- No AWS resources are created by this starter package.
