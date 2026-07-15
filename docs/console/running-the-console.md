---
description: >-
  How to run the Phase 0 Source Lock Console locally — backend (FastAPI +
  MongoDB) and frontend (React) — and drive a full ingestion run.
icon: play
---

# Running the console

The Console has two processes: a FastAPI backend (with MongoDB) and a React frontend. Bring up the backend first so the API is ready when the UI loads.

## Prerequisites

- **Python** 3.11+ and `pip`
- **Node.js** 18+ with **Yarn** (the frontend uses a `yarn.lock`)
- A running **MongoDB** instance
- LLM credentials for `emergentintegrations` (used for deep-read analysis)

{% hint style="warning" %}
The backend reads configuration from `backend/.env`. At minimum it expects `MONGO_URL` and `DB_NAME`. **Never commit real secrets** — keep API keys and tokens out of the repo and out of any operational report.
{% endhint %}

## Start the backend

{% stepper %}
{% step %}
### Install dependencies
```bash
cd backend
pip install -r requirements.txt
```
{% endstep %}

{% step %}
### Configure the environment
Create `backend/.env` with your `MONGO_URL`, `DB_NAME`, and LLM credentials.
{% endstep %}

{% step %}
### Run the API
```bash
uvicorn server:app --reload --port 8000
```
The API is served under the `/api` prefix — check `GET /api/status`.
{% endstep %}
{% endstepper %}

## Start the frontend

{% stepper %}
{% step %}
### Install dependencies
```bash
cd frontend
yarn install
```
{% endstep %}

{% step %}
### Run the dev server
```bash
yarn start
```
The app opens at [http://localhost:3000](http://localhost:3000) and talks to the backend `/api` routes.
{% endstep %}
{% endstepper %}

## Drive an ingestion run

1. Open the Console and press **Run ingestion** on the dashboard.
2. Watch progress until the run reports complete.
3. Browse the **Source Index**, open a few sources, and check the **Contradictions** register.
4. Review the five artifacts under **Artifacts**.
5. When satisfied, use **Operator Accept** to freeze Phase 0 into WAIT mode.

{% hint style="info" %}
Ingestion is idempotent — re-running it upserts by `sha256 + path` and will not duplicate records. See [Architecture](architecture.md) for the pipeline details.
{% endhint %}
