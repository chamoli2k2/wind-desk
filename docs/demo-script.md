# Recording guide — target 9 minutes 30 seconds

Record your screen and voice, then upload the recording to YouTube as **Unlisted**. This file is a guide, not a completed video. Add the actual video and Render links to the README before submitting. Run the app and CI checks first.

## Part 1 — customer pilot (0:00–4:45)

### 0:00–0:45 · Introduce the decision

“Wind Desk helps your day-ahead buying team see the wind forecast that was actually available before a purchase decision, and understand how it performed. This pilot uses only Elexon wind forecasts and actual generation. It does not claim to calculate your company's purchase volume without your demand and existing positions.”

### 0:45–2:00 · Decision desk

Open 15 January at 09:00. Point out that delivery is 16 January. Explain that 09:00 is a configurable assumption. Show the hourly forecast, the hindsight actuals and the day's forecast energy. Hover over points for exact values and open the audit table.

“The publication timestamp lets us prove this forecast existed before the cutoff. Later revisions cannot sneak into this view.”

Change the cutoff to 08:00 or 11:00, observe the result, then reset it to 09:00. Do not promise every change in cutoff produces a different forecast: it depends on publication times.

### 2:00–3:20 · Accuracy

Open Forecast accuracy. At the 09:00 default, all 744 hours are paired. The snapshot's MAE is about 2,039 MW and bias about +1,748 MW. Explain positive bias: actual wind was lower than forecast on average. RMSE is about 2,505 MW and gives large misses more weight. WAPE is about 18.07%.

“These are observations from this historical month, not a guarantee about tomorrow.”

Click 27 January to inspect a high-error day and its following-day delivery profile.

### 3:20–4:10 · Trust and export

Show Data & methodology. Explain hourly forecast versus half-hour actual alignment, missing-data handling and the national scope. Export the CSV to show that the analysis is reviewable outside the portal.

### 4:10–4:45 · Close the customer pitch

“The pilot gives the team one consistent view of available wind forecasts, their publication history and measured error. A next phase would bring in your load and contracted positions, then evaluate risk methods on an earlier training period and a separate holdout before making procurement recommendations.”

## Part 2 — technical review (4:45–9:30)

### 4:45–5:30 · Architecture

Show the directory tree. Explain React as the view, Flask controllers, snapshot model and analysis service. Describe the single Docker image: Node builds assets; a smaller Python runtime serves both assets and API. No production Node server is needed.

### 5:30–6:45 · Selection and alignment

Open `analysis.py`. Walk through the decision-to-delivery date calculation, `publishTime <= decision`, latest eligible revision, and the requirement for both half-hour actuals. Show the January 31 → February 1 test and no-lookahead test.

### 6:45–7:30 · Data ingestion

Open `ingest.py` and the snapshot provenance. Explain daily publication queries, four bounded concurrent requests, retries, duplicate conflict detection, validation and atomic snapshot replacement. The snapshot allows the demo to run without a live upstream API.

### 7:30–8:30 · API and frontend

Show input validation, the shared analysis used for CSV, and frontend loading/error handling. Discuss coverage counts rather than filling missing readings. Explain that actuals are retrospective and explicitly labelled.

### 8:30–9:30 · Deployment and checks

Show Dockerfile, `start.sh`, `render.yaml` and the test workflow. Explain Render's PORT binding and health check. Show the real test results from your machine or CI. Be clear about any tests still not run. Finish with scope limits: one historical month, no authentication or trading execution, and no portfolio inputs.

Stop before ten minutes. Do not submit without the actual unlisted video; the assignment says evaluation begins with it.
