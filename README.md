# ms_ai_classifier

Python FastAPI microservice for the Mi Cartera statement-ingestion workflow.

## Purpose

This service subscribes to `FILE_UPLOADED`, reads the stored PDF, extracts bank movements, normalizes them, classifies them with OpenAI Structured Outputs, persists the job/result, and publishes:

- `AI_CLASSIFICATION_STARTED`
- `AI_CLASSIFICATION_COMPLETED`
- `TRANSACTIONS_CLASSIFIED`
- `AI_CLASSIFICATION_FAILED`

## Recommended event contract location

The cross-service source of truth lives at:

- [`contracts/events/mi_cartera_events.yaml`](../contracts/events/mi_cartera_events.yaml)

That is the best place in this repo to define event names because it is language-agnostic and usable by both Spring and Python services.

## HTTP endpoints

- `GET /health`
- `GET /api/v1/classification-jobs/{job_id}`
- `POST /api/v1/classification-jobs/{job_id}/corrections`
