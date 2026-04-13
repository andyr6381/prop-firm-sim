# Prop Firm Challenge Monte Carlo Simulator

A Python + Streamlit Monte Carlo simulator for modelling an Apex-style prop firm evaluation with a trailing drawdown.

The project answers two questions:

1. What happens if I trade my current plan?
2. Given my goals and risk tolerance, what risk size is recommended?

## What It Models

The default account model is:

- Profit target: `$3,000`
- Trailing drawdown distance: `$2,000`
- Trailing floor rises whenever a new equity high is reached

The simulator supports:

- Fixed risk
- Dynamic risk that halves below the equity peak
- Mechanical systems
- Discretionary systems with optional breakeven trades
- Hot streaks, cold streaks, and no-trade periods
- Aggressive, Balanced, Conservative, and Fastest Safe recommendations

## Architecture

### `prop_simulator.py`

This file is now a pure simulation engine built around explicit config and result objects.

Key objects:

- `SimulationConfig`
- `StreakConfig`
- `PathResult`
- `SimulationSummary`
- `Recommendation`
- `SimulationReport`

Key functions:

- `calculate_expectancy(config)`
- `simulate_one_path(config, risk_dollars, dynamic=False, seed=None)`
- `run_simulation(config, risk_dollars, dynamic=False, num_sims=None)`
- `build_simulation_report(config, fixed_risk_amount)`
- `sample_paths(...)`

There are no UI globals to mutate and no plotting side effects at import time.

### `app.py`

The Streamlit app is a thin UI layer that:

- Collects sidebar settings
- Builds a `SimulationConfig`
- Calls the engine
- Renders the recommendation matrix and charts

## Account Logic

Trailing drawdown is tracked as:

```text
trailing_floor = peak_equity - dd_limit
```

The simulation ends with one of three explicit outcomes:

- `pass`: equity reaches the profit target
- `breach`: equity falls below the trailing floor
- `timeout`: max simulation steps are reached first

This is intentionally different from the old version, which treated every non-pass as a “blow-up”.

## Strategy Modes

### Mechanical

Each executed trade is either:

- Winner = `profit_factor * risk`
- Loser = `-1 * risk`

### Discretionary

A configurable percentage of executed trades become breakeven scratches:

- `be_trade_percent = 20` means about 20% of executed trades return `0R`

The remaining executed trades still use the normal win/loss model.

## Streak Model

The default streak assumptions are:

- Hot streak start chance: `~4%`
- Hot streak win-rate shift: `+18%`
- Hot streak average duration: `~4 trades`
- Cold streak start chance: `~8%`
- Cold streak win-rate shift: `-22%`
- Cold streak average duration: `~6 trades`
- No-trade probability: `~22%`

No-trade periods affect simulation steps and chart progression, but they do not count as executed trades.

## Recommendation Styles

The app compares:

- Your Fixed Risk
- Your Dynamic Risk
- Aggressive Recommended
- Balanced Recommended
- Conservative Recommended
- Fastest Safe

Style intent:

- Aggressive: targets roughly `50–75%` pass odds and larger sizing, typically `35–60%` of DD
- Balanced: targets roughly `75–90%` pass odds, typically `20–35%` of DD
- Conservative: targets roughly `90–100%` pass odds, typically `10–20%` of DD
- Fastest Safe: searches more broadly for the quickest plan that still clears a safety floor

## Streamlit Output

The app shows:

- A recommendation matrix
- Four charts in a 2x2 layout
- Example equity paths
- Trailing drawdown lines
- Stats boxes with:
  - Pass %
  - Breach %
  - Timeout %
  - Average pass steps
  - Average pass trades

Chart x-axes are labelled as `Simulation Steps` because no-trade periods are included in the path progression.

## Run

### Streamlit App

```bash
streamlit run app.py
```

### Engine Usage

```python
from prop_simulator import SimulationConfig, build_simulation_report

config = SimulationConfig(
    profit_target=3000,
    dd_limit=2000,
    win_rate=0.60,
    profit_factor=1.6,
    strategy_mode="Mechanical",
    trader_style="Balanced",
)

report = build_simulation_report(config, fixed_risk_amount=250)
print(report.selected.risk_dollars)
print(report.selected.summary.pass_rate)
```

## Why This Refactor Matters

The new engine structure makes the project much easier to extend with future features such as:

- Days-to-pass constraints
- Trades-per-day modelling
- CSV trade-history upload
- Risk-of-ruin diagnostics
- Psychological stress scoring
