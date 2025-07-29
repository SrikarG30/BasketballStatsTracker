(function () {
  const { useState, useEffect, useRef } = React;

  /**
   * Root component of the Basketball Stats Tracker frontend. It fetches
   * available games from the API, allows the user to pick a game, and
   * displays both tabular and visual representations of the players' box
   * scores and computed metrics. Charts automatically refresh every
   * minute to mimic a live data feed.
   */
  function App() {
    const [games, setGames] = useState([]);
    const [selectedGame, setSelectedGame] = useState("");
    const [players, setPlayers] = useState([]);
    const [chartData, setChartData] = useState(null);
    const pointsChartRef = useRef(null);
    const tsChartRef = useRef(null);
    const momentumChartRef = useRef(null);
    const pointsChartInstance = useRef(null);
    const tsChartInstance = useRef(null);
    const momentumChartInstance = useRef(null);

    const API_BASE = "http://localhost:8000";

    // Fetch list of games on mount
    useEffect(() => {
      async function fetchGames() {
        try {
          const res = await fetch(`${API_BASE}/games`);
          const data = await res.json();
          setGames(data);
          if (data.length > 0) {
            setSelectedGame(data[0].gameId);
          }
        } catch (err) {
          console.error("Failed to load games", err);
        }
      }
      fetchGames();
    }, []);

    // When a game is selected, fetch its players and chart data. The
    // callback is also registered on an interval to refresh the data
    // every 60 seconds, mimicking near real‑time updates.
    useEffect(() => {
      if (!selectedGame) return;
      let intervalId;
      async function loadGame() {
        try {
          const playersRes = await fetch(`${API_BASE}/game/${selectedGame}/players`);
          const playersData = await playersRes.json();
          setPlayers(playersData);
          const chartRes = await fetch(`${API_BASE}/game/${selectedGame}/charts`);
          const chartJson = await chartRes.json();
          setChartData(chartJson);
        } catch (err) {
          console.error("Failed to load game data", err);
        }
      }
      // initial load
      loadGame();
      // set up refresh interval
      intervalId = setInterval(loadGame, 60000);
      return () => clearInterval(intervalId);
    }, [selectedGame]);

    // Draw or update charts when chartData changes
    useEffect(() => {
      if (!chartData) return;
      // Utility to (re)create a chart
      function createChart(ctx, type, label, data, options = {}) {
        return new Chart(ctx, {
          type,
          data: {
            labels: chartData.labels,
            datasets: [
              {
                label,
                data,
                backgroundColor:
                  type === "bar"
                    ? "rgba(54, 162, 235, 0.6)"
                    : "rgba(255, 99, 132, 0.6)",
                borderColor:
                  type === "bar"
                    ? "rgba(54, 162, 235, 1)"
                    : "rgba(255, 99, 132, 1)",
                borderWidth: 1,
                fill: false,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
              },
            },
            ...options,
          },
        });
      }
      // Destroy previous instances to avoid overlaying multiple charts
      if (pointsChartInstance.current) pointsChartInstance.current.destroy();
      if (tsChartInstance.current) tsChartInstance.current.destroy();
      if (momentumChartInstance.current) momentumChartInstance.current.destroy();
      // Create new charts
      if (pointsChartRef.current) {
        const ctx1 = pointsChartRef.current.getContext("2d");
        pointsChartInstance.current = createChart(
          ctx1,
          "bar",
          "Points",
          chartData.datasets.points
        );
      }
      if (tsChartRef.current) {
        const ctx2 = tsChartRef.current.getContext("2d");
        tsChartInstance.current = createChart(
          ctx2,
          "bar",
          "True Shooting %",
          chartData.datasets.true_shooting
        );
      }
      if (momentumChartRef.current) {
        const ctx3 = momentumChartRef.current.getContext("2d");
        momentumChartInstance.current = createChart(
          ctx3,
          "line",
          "Momentum (Plus/Minus)",
          chartData.datasets.momentum
        );
      }
    }, [chartData]);

    return React.createElement(
      "div",
      { className: "container" },
      React.createElement("h1", null, "Basketball Stats Tracker"),
      // Game selector
      React.createElement(
        "div",
        null,
        React.createElement(
          "label",
          { htmlFor: "game-select" },
          "Select Game: "
        ),
        React.createElement(
          "select",
          {
            id: "game-select",
            value: selectedGame,
            onChange: (e) => setSelectedGame(e.target.value),
          },
          games.map((g) =>
            React.createElement(
              "option",
              { key: g.gameId, value: g.gameId },
              `${g.game_date} – ${g.teams[0]}`
            )
          )
        )
      ),
      // Players table
      React.createElement(
        "table",
        null,
        React.createElement(
          "thead",
          null,
          React.createElement(
            "tr",
            null,
            [
              "Player",
              "Team",
              "Position",
              "Minutes",
              "PTS",
              "REB",
              "AST",
              "STL",
              "BLK",
              "TO",
              "TS%",
              "Efficiency",
              "+/-",
            ].map((hdr) =>
              React.createElement("th", { key: hdr }, hdr)
            )
          )
        ),
        React.createElement(
          "tbody",
          null,
          players.map((p) =>
            React.createElement(
              "tr",
              { key: p.personId },
              [
                p.personName,
                `${p.teamTricode}`,
                p.position || "-",
                p.minutes,
                p.points,
                p.rebounds,
                p.assists,
                p.steals,
                p.blocks,
                p.turnovers,
                p.true_shooting.toFixed(3),
                p.efficiency.toFixed(2),
                p.plusMinus,
              ].map((val, idx) =>
                React.createElement(
                  "td",
                  { key: idx },
                  val
                )
              )
            )
          )
        )
      ),
      // Charts container
      React.createElement(
        "div",
        { className: "charts" },
        React.createElement(
          "div",
          { className: "chart-container" },
          React.createElement("canvas", { ref: pointsChartRef })
        ),
        React.createElement(
          "div",
          { className: "chart-container" },
          React.createElement("canvas", { ref: tsChartRef })
        ),
        React.createElement(
          "div",
          { className: "chart-container" },
          React.createElement("canvas", { ref: momentumChartRef })
        )
      )
    );
  }

  // Mount the application
  const root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(React.createElement(App));
})();