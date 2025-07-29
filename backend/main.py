"""FastAPI backend for the Basketball Stats Tracker.

This backend exposes a few endpoints that allow a React/JavaScript frontend
to query game data, compute advanced metrics (True Shooting percentage and
a simplified PER-like efficiency rating), and return chart-friendly
structures. A lightweight CSV file lives under ``data/sample_box_scores.csv``
and is loaded when the application starts. In a real world scenario you
would ingest live play‑by‑play or box score data from an external API
(for example, NBA Stats or balldontlie) but those services either
require authentication or are blocked in this environment. Therefore,
the application ships with a small, self‑contained dataset that makes
development and demonstration easier.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
from typing import List, Dict


# By default the application loads a sample dataset built from real NBA
# playoff data (Boston vs. Miami on April 21, 2024). If you wish to
# experiment with your own data, place a CSV file in ``backend/data``
# with the same header structure and update this constant accordingly.
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "real_box_scores.csv")


class PlayerStats(BaseModel):
    """Schema representing a single player's stats with computed metrics."""

    gameId: str
    teamId: int
    teamName: str
    teamTricode: str
    personId: int
    personName: str
    position: str
    minutes: str
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    turnovers: int
    true_shooting: float
    efficiency: float
    plusMinus: int


class GameInfo(BaseModel):
    """Schema used for listing games available in the dataset."""

    gameId: str
    game_date: str
    teams: List[str]


class ChartData(BaseModel):
    """Schema returned by the chart endpoint. It packages labels and datasets
    so the frontend can feed the values directly into Chart.js.
    """

    labels: List[str]
    datasets: Dict[str, List[float]]


def _load_data(path: str) -> pd.DataFrame:
    """Load the box score CSV into a pandas DataFrame, performing basic
    type conversions. This function is called once when the module is
    imported.

    Args:
        path: Path to the CSV file.

    Returns:
        A pandas DataFrame with properly typed numeric columns.
    """
    df = pd.read_csv(path)
    # Convert numeric columns from strings to numbers. Some numeric
    # columns might contain missing values or empty strings – coercing
    # errors to NaN then filling with zero keeps downstream math sane.
    numeric_cols = [
        "fieldGoalsMade",
        "fieldGoalsAttempted",
        "threePointersMade",
        "threePointersAttempted",
        "freeThrowsMade",
        "freeThrowsAttempted",
        "reboundsOffensive",
        "reboundsDefensive",
        "reboundsTotal",
        "assists",
        "steals",
        "blocks",
        "turnovers",
        "foulsPersonal",
        "points",
        "plusMinusPoints",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    # Convert teamId and personId to ints (they may already be ints).
    df["teamId"] = pd.to_numeric(df["teamId"], errors="coerce").astype(int)
    df["personId"] = pd.to_numeric(df["personId"], errors="coerce").astype(int)
    return df


# Global DataFrame loaded at import time. Keeping it global avoids reloading
# the CSV on every request, improving performance for repeated queries.
DATAFRAME = _load_data(DATA_PATH)


def _calculate_true_shooting(row: pd.Series) -> float:
    """Compute True Shooting percentage for a row of stats.

    TS% = Points / (2 * (FGA + 0.44 * FTA))

    If a player attempted no field goals or free throws, the denominator
    becomes zero. In that case we return 0.0.
    """
    fga = row["fieldGoalsAttempted"]
    fta = row["freeThrowsAttempted"]
    denom = 2 * (fga + 0.44 * fta)
    return (row["points"] / denom) if denom > 0 else 0.0


def _calculate_efficiency(row: pd.Series) -> float:
    """Compute a simple efficiency rating reminiscent of PER.

    The formula used is:

        efficiency = (PTS + REB + AST + STL + BLK)
                     - ((FGA - FGM) + (FTA - FTM) + TO)

    This isn't the official PER calculation from basketball-reference, but
    it captures the intuition that positive contributions (scoring and
    counting stats) should outweigh negative plays like missed shots and
    turnovers.
    """
    made = row["fieldGoalsMade"]
    attempted = row["fieldGoalsAttempted"]
    ftm = row["freeThrowsMade"]
    fta = row["freeThrowsAttempted"]
    rebounds = row["reboundsTotal"]
    assists = row["assists"]
    steals = row["steals"]
    blocks = row["blocks"]
    turnovers = row["turnovers"]
    points = row["points"]
    return (points + rebounds + assists + steals + blocks) - ((attempted - made) + (fta - ftm) + turnovers)


app = FastAPI(title="Basketball Stats Tracker API")

# Allow CORS so the React frontend (often served from another port) can
# request data without being blocked by the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/games", response_model=List[GameInfo])
def list_games() -> List[GameInfo]:
    """Return a list of unique games available in the dataset.

    Each entry contains the gameId, the game date, and a simple string
    describing the participating teams (e.g., "Celtics vs. Lakers").
    """
    games = []
    # Group by gameId to collect participating teams.
    for game_id, group in DATAFRAME.groupby("gameId"):
        # Use the first date found (they're identical for a given game).
        date = group["game_date"].iloc[0]
        teams = group[["teamName"]].drop_duplicates()["teamName"].tolist()
        games.append(
            GameInfo(
                gameId=str(game_id),
                game_date=str(date),
                teams=[f"{teams[0]} vs. {teams[1]}" if len(teams) > 1 else teams[0]],
            )
        )
    return games


@app.get("/game/{game_id}/players", response_model=List[PlayerStats])
def game_players(game_id: str) -> List[PlayerStats]:
    """Return the list of players for a given game with computed metrics.

    Args:
        game_id: The ID of the game to query.

    Raises:
        HTTPException: If the game is not found.

    Returns:
        A list of PlayerStats objects.
    """
    df_game = DATAFRAME[DATAFRAME["gameId"].astype(str) == str(game_id)]
    if df_game.empty:
        raise HTTPException(status_code=404, detail="Game not found")
    players: List[PlayerStats] = []
    for _, row in df_game.iterrows():
        ts = _calculate_true_shooting(row)
        eff = _calculate_efficiency(row)
        players.append(
            PlayerStats(
                gameId=str(row["gameId"]),
                teamId=int(row["teamId"]),
                teamName=row["teamName"],
                teamTricode=row["teamTricode"],
                personId=int(row["personId"]),
                personName=row["personName"],
                position=row.get("position", ""),
                minutes=row["minutes"],
                points=int(row["points"]),
                rebounds=int(row["reboundsTotal"]),
                assists=int(row["assists"]),
                steals=int(row["steals"]),
                blocks=int(row["blocks"]),
                turnovers=int(row["turnovers"]),
                true_shooting=round(ts, 3),
                efficiency=round(eff, 2),
                plusMinus=int(row["plusMinusPoints"]),
            )
        )
    return players


@app.get("/game/{game_id}/charts", response_model=ChartData)
def game_charts(game_id: str) -> ChartData:
    """Return chart‑friendly data for a given game.

    This endpoint aggregates several arrays of values keyed by player names.
    The frontend can map these values to multiple charts (points per player,
    true shooting percentage, and a pseudo‑momentum line using plus/minus).
    """
    df_game = DATAFRAME[DATAFRAME["gameId"].astype(str) == str(game_id)]
    if df_game.empty:
        raise HTTPException(status_code=404, detail="Game not found")
    labels: List[str] = []
    points: List[float] = []
    ts_list: List[float] = []
    momentum: List[float] = []
    for _, row in df_game.iterrows():
        labels.append(row["personName"])
        points.append(float(row["points"]))
        ts_list.append(round(_calculate_true_shooting(row), 3))
        momentum.append(float(row["plusMinusPoints"]))
    data = ChartData(
        labels=labels,
        datasets={
            "points": points,
            "true_shooting": ts_list,
            "momentum": momentum,
        },
    )
    return data
