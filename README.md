<!-- MARKET-SNAPSHOT-START -->
| Market    | Updated   | Trend      | Strategy          | Signal | Since          |
| --------- | --------- | ---------- | ----------------- | ------ | -------------- |
| NIFTY 50  | 11:55 IST | 🔴 Bear     | Buy NIFTY 25-Aug-2026-23700-PE<br>Sell NIFTY 25-Aug-2026-22950-PE | Active | Today, 11:27   |
| BANKNIFTY | 11:55 IST | 🟡 Neutral  | No Trade          | Hold   | Today, 11:27   |
<!-- MARKET-SNAPSHOT-END -->

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
# Portfolio Intelligence

A personal market and options decision engine for systematic premium selling, directional overlays, and adaptive learning.

## What this does

- Scans market regime indicators
- Scores portfolio risk and exposure
- Suggests exactly one highest-expected-value trade
- Learns from outcomes over time

## Core idea

The engine treats your portfolio as a two-sided premium-selling book:
- short calls
- short puts
- optional directional hedges

It aims to improve the whole portfolio, not just a single position.

## Planned structure

- `config/` — scoring weights and risk limits
- `engine/` — indicator, portfolio, and trade selection logic
- `portfolio/` — position snapshots and buying power state
- `recommendations/` — daily recommendation outputs
- `outcomes/` — executed trade results and learning data
- `reports/` — daily and weekly reports
- `docs/` — design notes and operating rules

## Status

Initial scaffold.

## Backtesting

Run a reproducible local NIFTY backtest with the included OHLCV dataset:

```bash
uv run pie backtest-market ^NSEI --data-path data/market/nifty50_25years_ohlcv_1999_2026.csv
```

The report evaluates directional trend signals against index returns; it does not model option-spread pricing.
