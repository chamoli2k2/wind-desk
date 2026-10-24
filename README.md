# Wind Desk

A January 2026 wind forecast review tool for a GB day-ahead power desk. React frontend, Flask backend, one Docker container. Flask serves both the API and the compiled frontend through Gunicorn.

**Deployment:** prepared for Render; not deployed yet. Add your Render URL here after deployment.
**Video:** add your unlisted YouTube link before submitting. A timed recording guide is in `docs/demo-script.md`.

## Run with Docker

```sh
docker compose up --build
```

Open http://localhost:10000. The real Elexon snapshot is included, so startup does not need an API key or an Elexon download.

## Deploy on Render

1. Extract this folder and push its contents to a GitHub repository. For the assignment, use a public repo with an anonymous name, such as `q7m4v9`.
2. In Render, select **New → Blueprint**, connect the repository and apply `render.yaml`. Alternatively, create a **Web Service**, choose **Docker**, and set the health check to `/api/health`.
3. Keep the repository root as the build context. Do not set a separate Node build command or Flask start command. The Dockerfile builds React, and `start.sh` starts Gunicorn.
4. Open the generated `https://<service-name>.onrender.com` URL. Check the decision desk and export button. Put the real URL above before submitting.

The service binds to `0.0.0.0:$PORT` (default 10000). No database, paid disk or separate frontend service is needed. The Blueprint selects Render's free plan; review its current limitations before using it for a client demo. Data is bundled into the image and survives redeploys. To update it, regenerate the snapshot locally and commit it.

Render docs: [Docker](https://render.com/docs/docker), [port binding](https://render.com/docs/web-services#port-binding), [Blueprints](https://render.com/docs/blueprint-spec).

## Local development

Python 3.12 and Node 22:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
python -m flask --app backend:create_app run --port 8000
```

In a second terminal, run `npm run dev` and open the Vite URL. Vite proxies `/api` to Flask. Production needs only the Docker container. On Windows, activate the virtual environment with `.venv\Scripts\activate`.

## What the app does

- Reconstructs the latest forecast available at a configurable decision cutoff.
- Shows the following day's hourly forecast and actual wind, signed errors and publication timestamps.
- Compares daily and monthly MAE, RMSE, bias and WAPE, with coverage counts.
- Exports all 744 delivery hours with their selected publication times as CSV.

The default cutoff is 09:00 London time, an editable pilot assumption rather than a claimed exchange deadline. January is GMT, so London and UTC are the same for this dataset.

## Data and calculations

Decision dates are **1–31 January 2026**, so delivery dates are **2 January–1 February 2026**. This intentionally includes February 1 and excludes January 1 delivery.

Data comes only from Elexon:

- [WINDFOR](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream): query publication windows to retain forecast revisions.
- [FUELHH](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream): retain only `fuelType = WIND`.

WINDFOR in the downloaded dataset is hourly. Each forecast is compared with the mean of the two FUELHH half-hour readings in that hour. Both actual readings must exist. Missing values stay missing and are excluded from paired metrics.

For each target hour, select the maximum `publishTime` that is **at or before** the prior-day cutoff. Selection is per target, so publication times may differ across hours. Publication history starts on 30 December 2025; the app does not substitute older unavailable forecasts. Source response hashes, query URLs and retrieval time are stored in `data/snapshot.json`. Duplicate conflicts cause ingestion to fail rather than silently choosing a value.

Error = forecast − actual. Positive error means less wind was delivered than forecast.

| Metric | Definition |
| --- | --- |
| MAE, MW | Mean absolute error |
| RMSE, MW | Square root of mean squared error |
| Bias, MW | Mean signed error |
| WAPE, % | 100 × total absolute error / total actual generation |

Hourly MW summed over one-hour intervals gives MWh; divide by 1,000 for GWh. Energy totals are labelled partial when forecast hours are missing. WAPE is unavailable when the denominator is zero. The month summary pools paired hours; it does not average daily percentages.

At the default 09:00 cutoff, the bundled snapshot has 744/744 paired hours: MAE **2,038.91 MW**, RMSE **2,504.76 MW**, bias **+1,747.89 MW**, WAPE **18.07%**. These are retrospective results, not confidence bounds or a trading recommendation.

The series covers GB wind visible to the system operator. National wind is not the client's demand or contracted portfolio. The app cannot calculate how much the client should buy without those additional inputs. Actuals are the retrieved historical benchmark, not observations available at each decision cutoff. Forecast-selection lookahead is prevented; later actual revisions remain a benchmark limitation.

### Refresh the snapshot

```sh
python -m backend.ingest
python -m unittest discover -s tests -v
```

Run from the repository root with requirements installed. Ingestion retries transient failures, validates timestamps and generation, deduplicates records, and replaces the snapshot atomically only when the whole download succeeds. It is an explicit maintenance command, not a public web endpoint. `DATA_DIR` can override the data folder.

## Structure

```text
backend/
  __init__.py             Flask factory and static React routes
  controllers/api.py      JSON, CSV and health endpoints; request validation
  models/repository.py    Snapshot access and modification-aware read cache
  services/analysis.py    As-of selection, hourly alignment and metrics
  ingest.py               Elexon download and snapshot validation
frontend/
  src/main.jsx            Decision desk, accuracy report and methodology views
  src/styles.css          Responsive styling
  vite.config.js          Build output and development API proxy
  index.html              React entry page
data/snapshot.json       Real Elexon records and retrieval provenance
tests/                   Selection, missing-data, metrics and API tests
docs/                    Review notes and timed video guide
.github/workflows/       Tests, frontend build and container smoke test
Dockerfile               React build stage and non-root Python runtime
compose.yaml             Local single-container startup
render.yaml              Render Docker web service configuration
start.sh                 Gunicorn startup using Render's PORT
requirements*.txt        Python dependencies
package.json             Frontend dependencies and scripts
```

MVC here means controllers handle HTTP, the model reads the snapshot, React provides the views, and services own the analysis. JSON is enough for this fixed-month, read-only pilot; adding a database would not improve the core decision workflow.

## Checks and known limits

```sh
python -m unittest discover -s tests -v
npm run build
docker build -t wind-desk .
```

The analysis tests and full-snapshot coverage checks passed during development. Package registry downloads were blocked in the build workspace, so the Flask API tests, React production build, browser checks and Docker runtime were not verified there. Docker was also unavailable. The included GitHub workflow runs those checks when you push. Do not treat deployment as verified until that workflow and Render's build succeed.

Direct dependency versions are pinned. A generated npm lockfile is not included because dependency installation was blocked; generate and commit `package-lock.json` after the first successful `npm install`, then use `npm ci` in Docker and CI for repeatable transitive dependencies.

This is a public, read-only pilot. There is no authentication, trading integration, live refresh or portfolio model. Google Fonts is optional presentation styling; system fonts are used if it is unavailable.

## AI assistance

OpenAI ChatGPT/Codex was used to help research the Elexon endpoints, write code, create tests and draft documentation. Verification performed and remaining checks are listed above.
