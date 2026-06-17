# HealthSenseAI

HealthSenseAI is a FastAPI and static-frontend MVP for educational symptom checking, ML-based disease prediction, Gemini-assisted explanations, PDF reports, nearby hospital discovery, and admin analytics.

## Local Startup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set values.
4. Start the backend:

```powershell
uvicorn backend.main:app --reload
```

5. Open `frontend/index.html` in a browser, or serve `frontend/` with any static file server.

## ML Artifacts and Data Files

- `Final_Augmented_dataset_Diseases_and_Symptoms.csv` is required only for retraining the model.
- Runtime inference does not read the CSV. The API uses the saved artifacts:
  - `backend/ml/model.joblib`
  - `backend/ml/label_encoder.joblib`
  - `backend/ml/symptom_columns.json`
- For deployment, the CSV can be omitted as long as those artifacts are already present in the environment.

## Environment Variables

`DEBUG`: `true` for local development, `false` for production. Common values like `release` and `production` are parsed as false.

`ENVIRONMENT`: `development`, `test`, or `production`.

`JWT_SECRET_KEY`: required in production. Use a long random secret.

`DATABASE_URL`: SQLAlchemy database URL. Defaults to local SQLite.

`GEMINI_API_KEY`: optional. If omitted, the app uses a local educational fallback response.

`CORS_ORIGINS`: comma-separated production browser origins.

## Testing

```powershell
python -m pytest
```

The test suite uses `test_healthsense.db` and resets tables between tests.

## Deployment

Docker:

```powershell
docker build -t healthsenseai .
docker run -p 8000:8000 --env-file .env healthsenseai
```

Render:

1. Create a new Blueprint from this repository.
2. Use `render.yaml`.
3. Set `JWT_SECRET_KEY`, `DATABASE_URL`, `GEMINI_API_KEY` if available, and `CORS_ORIGINS`.
4. Confirm `/api/health` returns `healthy`.
5. The CSV file is not needed at runtime for the deployed API; only the saved ML artifacts are used for prediction.

## Database Migration Strategy

The MVP currently creates tables with SQLAlchemy metadata at startup. For production changes after launch, use Alembic migrations before modifying model fields on live data. Existing symptom rows stored as comma-separated text are still readable; new predictions store symptoms as JSON text.

## Medical Disclaimer

HealthSenseAI is educational software. It does not diagnose disease or replace professional medical advice, diagnosis, or treatment.
