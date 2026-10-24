# Technical review notes

## Request path

Browser → Gunicorn → Flask controller → analysis service → snapshot repository.
React uses same-origin relative API URLs. There is no production Vite process, CORS setup, separate frontend deployment or browser access to Elexon.

GET `/api/analysis?cutoff=09:00` returns 31 decision days, each with 24 target hours, selected forecasts, publication timestamps, actuals and errors. GET `/api/export` applies the same analysis path and returns CSV. GET `/api/health` is a lightweight process health check, not a data-quality certification.

The repository caches parsed JSON by path and modification timestamp. Analysis runs per request over roughly 18,000 forecast records. This keeps the code simple for a fixed month. If the archive grows, index `(target_time, publish_time)` in a database and cache cutoff results; do not keep extending this in-memory scan indefinitely.

## Important decisions

1. Query forecast publications, not a latest-only endpoint. A latest-only dataset would contaminate the backtest with information unavailable before the trade.
2. Select the latest eligible publication independently for each target. Missing target hours remain visible through coverage counts.
3. Match hourly forecasts to the mean of both half-hour actuals. No interpolation or zero-fill.
4. Separate historical evaluation from decision-time knowledge. Actuals are visible for the pilot but labelled hindsight. Monthly metrics are not used as a decision-time risk band.
5. Fix the decision month, not the delivery month. 31 January buys for 1 February.
6. Keep the source snapshot immutable during ordinary requests. An offline ingestion command validates a replacement before an atomic rename.
7. Make forecast-vintage availability and assumptions inspectable in the UI, API and CSV.

## Scope and risks

No prices, load, positions, embedded-wind corrections or client exposure assumptions have been introduced. This avoids presenting national wind error as a utility's order quantity. One-month performance may not generalise to another season. Historical actual revisions may change results on refresh.

Forecast rows are validated as hourly and actuals as half-hourly. A change in source resolution fails ingestion. Concurrent upstream calls are limited to four, with bounded retry attempts and timeouts. The application does not expose a refresh endpoint, so anonymous traffic cannot trigger large downloads.

Dependency downloads, frontend/browser QA, Flask execution and Docker build remain to be verified in an environment with package registry access. See README and GitHub workflow. A lockfile should be committed after a successful installation.

## Review order

Start with `backend/services/analysis.py`, then its tests, then `backend/ingest.py`. Review the controller validation and shared CSV analysis path. Finally inspect React's loading/error states, cutoff controls, coverage labels, and the Docker/Render files.
