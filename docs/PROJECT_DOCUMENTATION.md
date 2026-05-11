# Smart Irrigation Project Documentation

## Project Overview

Smart Irrigation is an MLOps/DevOps project for predicting whether irrigation is required from sensor and weather inputs. The system combines:

- A FastAPI backend that exposes prediction, simulation, history, analysis, anomaly, and metrics endpoints.
- A scikit-learn machine learning model stored as `models/model.pkl`, with a matching scaler in `models/scaler.pkl`.
- A SQLite database used to persist prediction history.
- A React/Vite frontend for dashboarding, manual control, scheduling, history, and settings.
- DVC, MLflow, Docker, Prometheus, Grafana, Jenkins, and GitHub Actions support.

The main functional objective is to help decide whether a parcel should be irrigated based on:

- `soil_moisture`
- `temperature`
- `humidity`
- `rainfall`
- `sunlight_hours`

The API returns a binary decision:

- `1`: irrigation recommended
- `0`: irrigation not recommended

## Architecture

The application is organized as a small full-stack ML system:

```text
Sensor/weather values
        |
        v
React frontend or API client
        |
        v
FastAPI backend
        |
        +--> Input validation
        +--> StandardScaler transform
        +--> RandomForest prediction
        +--> SQLite prediction logging
        +--> Prometheus metrics
        |
        v
Frontend dashboards, history, analysis, anomaly views
```

Main runtime components:

- Backend service: `api/main.py`
- Database layer: `api/database.py`
- Error handling layer: `error_handlers.py`
- Frontend app: `irrigation_frontend/src`
- ML training pipeline: `src/train_pipeline.py`
- Model artifacts: `models/model.pkl`, `models/scaler.pkl`
- Monitoring stack: `monitoring/`, Prometheus, Grafana
- Container orchestration: `docker-compose.yml`

## Technologies

Backend and ML:

- Python
- FastAPI
- Uvicorn
- Pydantic
- NumPy
- Pandas
- scikit-learn
- joblib
- SQLite
- Prometheus client
- MLflow
- DVC
- PyYAML
- pytest
- httpx

Frontend:

- React 18
- Vite 5
- JavaScript ES modules
- CSS design tokens in `tokens.css`
- Native `fetch` API

Infrastructure and DevOps:

- Docker
- Docker Compose
- Nginx for production frontend serving
- Prometheus
- Grafana
- Jenkins
- GitHub Actions

## Folder Structure

```text
.
|-- api/
|   |-- main.py                    # FastAPI app, routes, model loading, metrics
|   |-- database.py                # SQLite schema and query functions
|   `-- train_model.py             # Additional model training script
|-- data/
|   |-- Smart_Farming_Crop_Yield_2024.csv
|   `-- meteo.csv.csv
|-- docs/
|   |-- CONCEPTS_INTEGRES.md
|   `-- PROJECT_DOCUMENTATION.md
|-- irrigation_frontend/
|   |-- src/
|   |   |-- app.jsx                # React app shell and page selection
|   |   |-- main.jsx               # React entrypoint
|   |   |-- tokens.css             # UI styling
|   |   |-- services/api.js        # API client
|   |   |-- hooks/useData.js       # Data hooks for simulation/history/predict
|   |   |-- components/            # Sidebar and reusable UI components
|   |   `-- pages/                 # Dashboard, Control, Schedule, History, Settings
|   |-- Dockerfile                 # Dev frontend container
|   |-- Dockerfile.prod            # Production Nginx build
|   |-- nginx.conf
|   |-- package.json
|   `-- vite.config.js
|-- models/
|   |-- model.pkl                  # Trained RandomForest model
|   `-- scaler.pkl                 # StandardScaler
|-- monitoring/
|   |-- prometheus.yml
|   `-- grafana/provisioning/
|-- notebooks/
|-- src/
|   |-- train_pipeline.py          # Main reproducible training pipeline
|   |-- preprocessing.py
|   |-- utils.py
|   |-- automl_train.py
|   `-- train.py
|-- tests/
|   |-- test_api.py
|   `-- test_database.py
|-- docker-compose.yml
|-- Dockerfile
|-- dvc.yaml
|-- params.yaml
|-- requirements.txt
|-- Jenkinsfile
`-- README.md
```

## Workflow

### Development Workflow

1. Install Python dependencies from `requirements.txt`.
2. Start the backend with Uvicorn.
3. Start the frontend with Vite.
4. Use the frontend pages or direct API calls to submit predictions.
5. Prediction requests are validated, transformed, predicted, and logged.
6. History and analysis pages read from SQLite through API endpoints.

Typical backend command:

```bash
uvicorn api.main:app --reload --port 8000
```

Typical frontend command:

```bash
cd irrigation_frontend
npm install
npm run dev
```

### ML Workflow

1. Training parameters are stored in `params.yaml`.
2. DVC runs the training stage defined in `dvc.yaml`.
3. `src/train_pipeline.py` loads the dataset, normalizes columns, creates a target if missing, splits data, scales features, trains a `RandomForestClassifier`, logs metrics to MLflow, and saves artifacts.
4. The generated artifacts are written to `models/model.pkl` and `models/scaler.pkl`.
5. Runtime API loads those artifacts at startup/import time.

The training pipeline normalizes CSV export columns to the canonical feature names used by the API:

| CSV column variant | Canonical feature |
| --- | --- |
| `soil_moisture_%` | `soil_moisture` |
| `temperature_C` | `temperature` |
| `humidity_%` | `humidity` |
| `rainfall_mm` | `rainfall` |
| `sunlight_hours` | `sunlight_hours` |

MLflow logging is optional at runtime: if `mlflow` is installed, the run is tracked; if not, the model can still be trained and exported.

Training command:

```bash
python src/train_pipeline.py
```

DVC command:

```bash
dvc repro
```

## Backend

The backend is implemented in `api/main.py` with FastAPI.

Main responsibilities:

- Load `models/model.pkl` and `models/scaler.pkl` with joblib.
- Verify `MODEL_SHA256` and `SCALER_SHA256` before any `joblib.load()` call.
- Initialize the SQLite database on startup.
- Validate incoming sensor data.
- Scale inputs before inference.
- Run model prediction.
- Log predictions to SQLite.
- Expose recent history, daily analysis, and anomalies.
- Expose Prometheus metrics.
- Register structured error handlers.
- Apply CORS rules from `CORS_ORIGINS`.

Important files:

- `api/main.py`: HTTP routes, model loading, prediction logic, metrics middleware.
- `api/database.py`: database initialization, inserts, history queries, analysis queries, anomaly detection.
- `error_handlers.py`: custom exceptions and FastAPI exception handlers.

The backend also includes a simple HTML interface on `GET /`, but the main user interface is the React app in `irrigation_frontend`.

## Frontend

The frontend is a React/Vite application located in `irrigation_frontend`.

Main pages:

- Dashboard: periodically calls `/test/simulate` every 5 seconds and displays live simulated sensor metrics, prediction result, pump status, and model feature importance.
- Control: submits manual sensor values to `POST /predict`, shows the AI result, and includes local UI state for irrigation zones.
- Schedule: manages irrigation schedules in local React state only. There is no backend persistence for schedules yet.
- History: calls `/history`, `/analysis`, and `/anomalies` to show logs, aggregates, charts, and anomaly alerts.
- Settings: exposes frontend configuration controls, but most values are local UI state and are not persisted to the backend.

Frontend API layer:

- `irrigation_frontend/src/services/api.js`
- Uses `VITE_API_URL`, defaulting to `http://localhost:8000`.
- Wraps backend endpoints with `predict`, `simulate`, `getHistory`, `getAnalysis`, and `getAnomalies`.

Frontend data hooks:

- `useLiveSimulation(interval)`
- `useHistory()`
- `usePredict()`

## APIs

### `GET /`

Returns a basic HTML page with a manual prediction form, simulation button, and analysis charts.

### `POST /predict`

Runs a prediction and saves the result to SQLite.

Request body:

```json
{
  "soil_moisture": 45.0,
  "temperature": 28.5,
  "humidity": 60.0,
  "rainfall": 5.0,
  "sunlight_hours": 8.0
}
```

Response body:

```json
{
  "irrigation_needed": 1,
  "message": "Prediction message",
  "importance": {
    "soil": 0.4,
    "temp": 0.3,
    "humidity": 0.15,
    "rain": 0.1,
    "sun": 0.05
  }
}
```

Validation bounds:

| Field | Min | Max |
| --- | ---: | ---: |
| `soil_moisture` | 0 | 100 |
| `temperature` | -20 | 60 |
| `humidity` | 0 | 100 |
| `rainfall` | 0 | 500 |
| `sunlight_hours` | 0 | 24 |

Possible errors:

- `422 invalid_sensor_data`
- `500 model_error`
- `503 database_error`
- `500 internal_error`

### `GET /test/simulate`

Generates random sensor values and runs the same prediction flow as `/predict`.

Response includes:

- `simulated_input`
- `irrigation_needed`
- `message`
- `importance`

Important behavior: this endpoint calls `predict(fake_data)`, so every simulation also creates a database log entry.

### `GET /history`

Returns all prediction logs from the last 7 days, ordered by newest first.

### `GET /analysis`

Returns daily aggregates from the last 7 days:

- `date`
- `total_water`
- `irrigation_count`

### `GET /anomalies`

Returns prediction log rows whose `soil_moisture` value is considered an outlier using IQR detection over the last 7 days.

### `GET /metrics`

Returns Prometheus metrics.

Custom metrics:

- `irrigation_api_requests_total`
- `irrigation_api_request_duration_seconds`
- `irrigation_predictions_total`

## Database

The database is SQLite.

Database path:

```text
api/irrigation_history.db
```

The database file is created automatically by `init_db()` when the backend starts.

Table: `logs`

| Column | Type | Description |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Unique log ID |
| `timestamp` | DATETIME | Insert time, defaults to current timestamp |
| `soil_moisture` | REAL | Soil moisture percentage |
| `temperature` | REAL | Temperature |
| `humidity` | REAL | Air humidity percentage |
| `rainfall` | REAL | Rainfall in mm |
| `sunlight_hours` | REAL | Sunlight duration |
| `irrigation_needed` | INTEGER | Prediction result, 0 or 1 |
| `water_used` | REAL | Estimated water use |

Water calculation:

```text
water_used = FLOW_RATE_L_PER_MIN * IRRIGATION_DURATION_MIN
```

Current constants:

- `FLOW_RATE_L_PER_MIN = 2.0`
- `IRRIGATION_DURATION_MIN = 5.0`
- One irrigation cycle therefore logs `10.0 L`.

## Authentication

Protected API endpoints now require an API key.

Current behavior:

- The backend reads `IRRIGATION_API_KEY` from the environment.
- Protected endpoints accept the key through `X-API-Key` or `Authorization: Bearer <key>`.
- If `IRRIGATION_API_KEY` is not configured, protected endpoints fail closed with `503`.
- Invalid or missing keys return `401`.
- A simple per-client rate limit is controlled by `RATE_LIMIT_PER_MINUTE`, defaulting to `60`.
- The React frontend sends `VITE_API_KEY` as `X-API-Key`.

Important limitation: `VITE_API_KEY` is visible in a browser bundle. This is a useful immediate protection for private/internal deployments, but public production deployments should use real user authentication such as sessions, OAuth2, or JWT with role-based authorization.

## Model Artifact Integrity

The backend validates model artifacts before loading them with `joblib.load()`.

Required environment variables:

- `MODEL_SHA256`: trusted SHA-256 hash for `models/model.pkl`
- `SCALER_SHA256`: trusted SHA-256 hash for `models/scaler.pkl`

Current trusted hashes in `.env.production.example`:

- `MODEL_SHA256=a8ea3279dead981fbaefb2f720381e46cb14b6a1f26ca31dbdf1b48f79ef7e39`
- `SCALER_SHA256=d6873392ab5a3d5f81090f58d27ec0d868708e07131a5b9eb1f284e32999e040`

If either checksum is missing or does not match the file on disk, the backend refuses to load both artifacts and prediction endpoints return a model unavailable error. This reduces the risk of arbitrary code execution from tampered pickle/joblib files.

After each trusted retraining or model release, recalculate the hashes and update the deployment configuration before restarting the API.

## Deployment

### Docker Compose

`docker-compose.yml` defines five services:

- `api`: builds the root `Dockerfile`, exposes `8000`, mounts `models`, `data`, and `mlruns`.
- `frontend`: builds `irrigation_frontend/Dockerfile`, exposes Vite on `5173`, sets `VITE_API_URL=http://localhost:8000`.
- `mlflow`: runs MLflow UI on `5000`.
- `prometheus`: runs Prometheus on `9090` and scrapes `api:8000/metrics`.
- `grafana`: runs Grafana on `3000` with provisioned dashboards and datasource.

Start command:

```bash
docker compose up --build
```

Service URLs:

- API: `http://localhost:8000`
- Frontend dev server: `http://localhost:5173`
- MLflow: `http://localhost:5000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

### Backend Dockerfile

The root `Dockerfile`:

- Uses `python:3.9`.
- Installs `requirements.txt`.
- Copies the project.
- Starts `uvicorn api.main:app` on port `8000`.

### Frontend Dockerfiles

`irrigation_frontend/Dockerfile`:

- Development-oriented Node container.
- Runs Vite on `0.0.0.0:5173`.

`irrigation_frontend/Dockerfile.prod`:

- Multi-stage build.
- Builds static assets with Node.
- Serves them with Nginx on port `80`.

### CI/CD

GitHub Actions:

- Installs Python 3.11.
- Installs `requirements.txt`.
- Runs `pytest -q`.

Jenkins:

- Installs Python dependencies.
- Runs tests.
- Builds Docker image `irrigation-api:latest`.

## Strengths

- Clear separation between backend, frontend, ML pipeline, tests, and monitoring.
- FastAPI provides automatic schema validation for request bodies.
- Additional physical sensor bounds are implemented in `error_handlers.py`.
- Model and scaler are externalized as artifacts.
- SQLite persistence makes the prototype easy to run locally.
- Prometheus metrics are already instrumented.
- Grafana provisioning exists for dashboarding.
- MLflow and DVC are integrated for experiment tracking and reproducible training.
- Docker Compose provides a complete local stack.
- Backend tests cover prediction, simulation, validation, history, and database behavior.
- The frontend is organized around reusable hooks and service functions.

## Weaknesses

- API key authentication exists for backend endpoints, but there is still no user/role authorization model.
- The simulation endpoint writes to the real prediction history, which can pollute analytics.
- Schedule and settings pages are mostly local UI state and are not persisted.
- SQLite is simple but limited for concurrent production workloads.
- The model is loaded globally at import time, which makes startup failures harder to recover from.
- The API and frontend both contain some overlapping UI functionality because `GET /` returns a separate HTML page while React provides the main app.
- The frontend has no automated tests.
- Error logs are written to a local file, which is not ideal for containers or distributed deployment.
- The code contains encoding/mojibake artifacts in several comments and UI strings.
- Test imports appear to assume top-level `main` and `database` modules, while the runtime files are under `api/`; this may require `PYTHONPATH` or import cleanup depending on the test environment.

## Security Problems

- No user-level authorization: there is no distinction between read-only users and users allowed to trigger irrigation-related actions.
- The current frontend API key is exposed to browser users because it is built into the SPA environment.
- CORS is configurable but currently permissive in methods and headers.
- `/metrics` is protected by API key, but still exposes operational details to any holder of the key.
- `/history` exposes recent sensor and irrigation records to any holder of the key.
- Rate limiting is in-memory and per-process, so it is not enough for horizontally scaled production.
- No request size limits are explicitly configured.
- SQLite database file is local and not encrypted.
- Model artifacts are checksum-verified before loading, but pickle/joblib remains a risky format if an attacker can update both the artifact and trusted checksum configuration.
- There is no secrets management pattern beyond environment variables and example env files.
- Containers do not explicitly run as non-root users.
- Frontend configuration fields can imply settings changes, but they are not secured or persisted.

## Performance Problems

- SQLite can become a bottleneck under concurrent writes.
- Pandas is used for history, aggregation, and anomaly reads on each request; this is fine for small data but inefficient for large logs.
- No database indexes are created on `timestamp`, so 7-day queries may slow down as `logs` grows.
- The simulation hook calls `/test/simulate` every 5 seconds and each call writes a log entry.
- The model and scaler are loaded once globally, which is efficient after startup but not resilient to hot model updates.
- `feature_importances_` is returned on every prediction; this is small, but static metadata could be cached or exposed separately.
- The API uses synchronous SQLite and model inference inside normal request handlers.
- Docker Compose mounts `models`, `data`, and `mlruns`, but not a dedicated persistent path for the SQLite database.
- The frontend dev container uses Vite, which is suitable for development but not production serving.

## Recommendations

- Replace browser-exposed API key auth with user authentication, such as JWT, session auth, or OAuth2.
- Add role-based authorization for admin, operator, and read-only views.
- Keep `/metrics` behind authentication and preferably restrict it to a private monitoring network.
- Move rate limiting to an edge proxy, API gateway, or shared store such as Redis for production.
- Split simulation logging from production prediction logging, or add a `source` column such as `manual`, `simulation`, `sensor`, `scheduled`.
- Add a real health endpoint such as `GET /health` instead of using `GET /` as an API availability check.
- Add indexes on `logs(timestamp)` and possibly `logs(irrigation_needed)`.
- Move database configuration to environment variables.
- Use PostgreSQL for production deployments.
- Add schedule persistence with a `schedules` table and CRUD API routes.
- Persist settings in the backend or remove controls that do not actually change backend behavior.
- Add frontend tests with Vitest and React Testing Library.
- Clean up import paths in tests so they consistently use `api.main` and `api.database`.
- Add structured logging to stdout for containers.
- Keep artifact checksum verification and consider adding signed artifacts for `model.pkl` and `scaler.pkl`.
- Pin Docker image patch versions and consider security scanning.
- Run containers as non-root where possible.
- Add model metadata endpoint with model version, training date, metrics, and feature list.
- Add OpenAPI documentation notes for each endpoint.

## Future Improvements

- Integrate real IoT sensor ingestion instead of random simulation.
- Add MQTT or another message broker for real-time sensor streams.
- Add automated irrigation actuation with safety limits and manual override.
- Add zone-level irrigation predictions and per-zone history.
- Add schedule persistence and schedule execution.
- Add alerts by email, SMS, Slack, or webhook.
- Add anomaly detection for all sensor fields, not only soil moisture.
- Add weather forecast integration.
- Add model retraining jobs triggered by new data.
- Add model registry and staged promotion from development to production.
- Add drift detection for sensor distributions and model predictions.
- Add explainability reports beyond RandomForest feature importance.
- Add backup and restore strategy for the production database.
- Add deployment manifests for cloud platforms or Kubernetes.
- Add HTTPS termination and production reverse proxy configuration.
- Add end-to-end tests covering frontend-to-backend flows.
- Add localization cleanup and consistent French/English UI text.
