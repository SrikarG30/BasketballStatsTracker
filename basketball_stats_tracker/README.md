# Basketball Stats Tracker

This repository contains a small full‑stack prototype that demonstrates how to
ingest basketball box–score data, compute advanced metrics and expose the
results to an interactive web frontend. The backend is built with
[FastAPI](https://fastapi.tiangolo.com/) and uses `pandas` for data
manipulation, while the frontend is a lightweight React/Chart.js application
embedded in a static HTML file.

## Motivation

The design of this application mirrors the project described on the résumé:

> *Built a full‑stack prototype with FastAPI backend and React frontend to
> ingest NBA play‑by‑play and box‑score data, compute advanced metrics
> (TS%, PER) in Python (Pandas), and expose REST endpoints for real‑time
> queries. Designed interactive Chart.js visualizations, shot charts,
> shooting percentages, and game momentum, refreshed every minute in the
> browser.*

Accessing live NBA data often requires API keys or scraping endpoints behind
rate limits. For the purposes of this demonstration, the repository ships
with a small sample CSV that mimics the structure of a true NBA box score
dataset. Each row contains the fields you would expect from real box scores
– game ID, team identifiers, player names, minutes played, made/attempted
field goals, three‑point attempts, free throws, rebounds, assists and other
counting stats. The header of the original dataset from which this format
was derived can be seen below【479577837952955†L0-L5】. The columns in the
sample file follow the same ordering and types.

## Project structure

```
basketball_stats_tracker/
├── backend/
│   ├── data/
│   │   └── sample_box_scores.csv  # example data used by the API
│   └── main.py                   # FastAPI application
├── frontend/
│   ├── index.html                # entry point for the React app
│   ├── app.js                    # React/Chart.js logic
│   └── styles.css                # simple styling
└── README.md                     # this file
```

### Backend

The backend loads the CSV file at startup and provides three endpoints:

* `GET /games` – returns a list of unique game IDs, their dates and a
  human‑readable description of the participating teams.
* `GET /game/{game_id}/players` – lists every player in a given game and
  computes two advanced metrics:
  * **True Shooting Percentage** (TS%) is calculated as
    `PTS / (2 * (FGA + 0.44 * FTA))`. The denominator reflects the
    possession cost of both field goal attempts and free throws【479577837952955†L0-L5】.
  * **Efficiency** – a simplified Hollinger‑style rating defined as
    `(PTS + REB + AST + STL + BLK) - ((FGA - FGM) + (FTA - FTM) + TO)`.
    This rewards positive contributions and penalises missed shots and
    turnovers.
* `GET /game/{game_id}/charts` – returns chart‑friendly arrays for points,
  TS% and plus/minus values indexed by player. The frontend uses this data
  to render bar and line charts.

To run the backend locally:

```bash
cd backend
python -m uvicorn main:app --reload
```

By default the API listens on port 8000 and has CORS enabled so it can be
queried from a browser served from another port or domain.

### Frontend

The frontend lives entirely in the `frontend` folder and is comprised of a
static HTML page, a JavaScript file and a stylesheet. It uses the UMD builds
of React, ReactDOM and Chart.js from public CDNs; there is no build step
required.

When the page loads it fetches the available games and populates a
drop‑down selector. Selecting a game triggers requests to the backend for
player statistics and chart data. The tables and charts update on the fly
and a timer refreshes the data every minute to emulate real‑time updates.

To serve the frontend locally you can use any static HTTP server (for
example `python -m http.server`). Assuming the backend is running on
`localhost:8000`, start a simple server in the `frontend` directory and
navigate to `http://localhost:8000/index.html`:

```bash
cd frontend
python -m http.server 3000
# then open http://localhost:3000 in your browser
```

Because the backend permits Cross‑Origin Resource Sharing, the frontend
hosted on port 3000 can freely fetch data from port 8000.

## Extending this prototype

* Replace `sample_box_scores.csv` with a real box score dataset. An example
  of the header and early rows from a genuine NBA playoff box score file
  show the type of information you would get【479577837952955†L0-L5】.
* Introduce a play‑by‑play dataset to build accurate shot charts and
  momentum graphs. You could augment the API to accept a game ID and
  return individual shot locations and timestamps, then use Chart.js or
  D3.js to visualise spatial data.
* Deploy the backend to a cloud provider (e.g. Render, Fly.io or Heroku)
  and the frontend to a static host (e.g. Vercel or GitHub Pages). Once
  deployed you can link to the live app from your résumé or portfolio.

## License

This project is provided for educational purposes and you are free to use
and modify it. The structure of the data and the API was inspired by
publicly available NBA box score datasets【479577837952955†L0-L5】.