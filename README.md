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