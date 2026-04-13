# Prop Firm Challenge Monte Carlo Simulator

A simple Python simulator for testing the probability of passing a prop firm evaluation account with a trailing drawdown...

## What It Models

The script simulates an Apex-style 50k evaluation account with:

- Profit target: $3,000
- Trailing drawdown: $2,000
- Configurable inputs:
  - Win rate
  - Reward:risk multiple (`profit_factor`)
  - Risk per trade

## Trading Modes

The simulator compares four approaches:

1. Fixed Risk
   - Uses the same dollar risk every trade.

2. Dynamic Risk
   - Uses full risk when at a new equity high.
   - Cuts risk in half while below the equity peak.

3. Safest Recommendation
   - Automatically tests many dynamic risk sizes.
   - Chooses the safest balance of:
     - High pass rate
     - Low blow-up rate
     - Reasonable number of trades to pass

4. Fastest Safe Recommendation
   - Chooses the fastest way to pass while still maintaining an acceptable pass rate.
   - Prioritizes fewer trades over maximum safety.

## Example Settings

At the top of `prop_simulator.py` you can adjust:

```python
profit_target = 3000
dd_limit = 2000
win_rate = 0.70
profit_factor = 1.5
fixed_risk_amount = 250
```
`profit_factor` is the reward:risk multiple of a winning trade.

Example:
- Risk = $250
- `profit_factor = 1.5`
- Winning trade = +$375
- Losing trade = -$250

## Output

The script runs thousands of Monte Carlo simulations and shows:

- Pass rate
- Blow-up rate
- Average trades needed to pass
- Four charts with example equity curves:
  1. Fixed Risk
  2. Dynamic Risk
  3. Safest Recommendation
  4. Fastest Safe Recommendation
- Matching trailing drawdown lines
- The safest and fastest-safe recommended risk sizes printed in the console

The stats box in the bottom-right of each chart shows:

- Pass Rate %
- Blow Rate %
- Average Trades

## Run

```bash
python prop_simulator.py
```# prop-firm-sim

# Prop Firm Challenge Monte Carlo Simulator

A Python Monte Carlo simulator for testing the probability of passing an Apex-style prop firm evaluation account with a trailing drawdown.

The simulator is designed to model both:

- Mechanical systems
- Discretionary systems with breakeven trade management

---

## What It Models

The script simulates a typical Apex 50k evaluation account with:

- Profit Target: $3,000
- Trailing Drawdown Limit: $2,000
- Dynamic trailing floor that moves up as new equity highs are made

User-configurable inputs:

- Win Rate
- Reward : Risk multiple (`profit_factor`)
- Fixed risk per trade
- Mechanical vs Discretionary execution style
- Optional breakeven trade percentage for discretionary systems

---

## Trading Modes

The simulator compares four approaches:

### 1. Fixed Risk

Uses the same dollar risk every trade.

Example:
- Risk $250 every trade

### 2. Dynamic Risk

Uses full risk while at a new equity high.

When the account is below the previous peak, risk is cut in half.

Example:
- Risk $250 at highs
- Risk $125 while in drawdown

### 3. Safest Recommendation

Automatically tests many dynamic risk sizes and chooses the safest overall option.

The recommendation prioritizes:

- Highest pass rate
- Lowest blow-up rate
- Reasonable number of trades required to pass

### 4. Fastest Safe Recommendation

Finds the quickest way to pass while still maintaining an acceptable pass probability.

The recommendation prioritizes:

- Fewest trades to pass
- Still keeping pass rate high enough to remain realistic

---

## Mechanical vs Discretionary Systems

### Mechanical Mode

Mechanical mode assumes every trade is either:

- Full winner = `profit_factor` R
- Full loser = -1R

Example:

- Win Rate = 60%
- Reward : Risk = 1.6R
- Risk = $250

Then:

- Winning trade = +$400
- Losing trade = -$250

### Discretionary Mode

Discretionary mode works the same way, but allows a percentage of trades to become breakeven scratches instead of full wins or losses.

Example:

- Breakeven Trades = 20%

Then 20% of trades produce 0R, while the remaining trades still use the normal win/loss logic.

This better reflects real discretionary trading with partials, breakeven management, and active trade management.

---

## Streak Modeling

The simulator includes realistic streak behavior rather than assuming every trade is completely independent.

### Hot Streaks

Occasionally the strategy enters a period where performance temporarily improves.

Typical settings:

- ~4% chance to start
- Win rate increases by about +18%
- Average length ≈ 4 trades

### Cold Streaks

More commonly, the strategy enters a losing period where the win rate temporarily drops.

Typical settings:

- ~8% chance to start
- Win rate decreases by about -22%
- Average length ≈ 6 trades

### Normal Periods

Most trades occur at the user's base win rate.

### No-Trade Periods

The simulator also includes quiet periods with no valid setup.

- ~22% probability of no trade

This creates more realistic equity curves and more natural clusters of wins and losses.

---

## Example Settings

```python
profit_target = 3000
dd_limit = 2000
win_rate = 0.60
profit_factor = 1.6
fixed_risk_amount = 250
strategy_mode = "Mechanical"
be_trade_percent = 20
```

`profit_factor` is the reward : risk multiple of a winning trade.

Example:

- Risk = $250
- `profit_factor = 1.6`
- Winning trade = +$400
- Losing trade = -$250

---

## Output

The simulator runs thousands of Monte Carlo simulations and displays:

- Pass Rate
- Blow-Up Rate
- Average Trades Needed To Pass
- Recommended safest risk size
- Recommended fastest-safe risk size

It also produces four charts:

1. Fixed Risk
2. Dynamic Risk
3. Safest Recommendation
4. Fastest Safe Recommendation

Each chart shows:

- 3 representative equity curves
- Matching trailing drawdown lines
- A bottom-right stats box containing:
  - Risk Size
  - Pass Rate
  - Blow Rate
  - Average Trades

---

## Run

```bash
python prop_simulator.py
```

For the Streamlit version:

```bash
streamlit run app.py
```
# Prop Firm Challenge Monte Carlo Simulator

A Monte Carlo simulator for modelling Apex-style prop firm evaluation accounts with a trailing drawdown.

The project consists of:

- `prop_simulator.py` → core simulation engine
- `app.py` → Streamlit UI and recommendation dashboard

The simulator is designed to answer two different questions:

1. "What happens if I trade my current plan?"
2. "Given my goals and risk tolerance, what is the best way to size the account?"

---

# Project Structure

## `prop_simulator.py`

Contains all simulation logic:

- Trailing drawdown tracking
- Fixed and dynamic risk sizing
- Hot / cold streak modelling
- Mechanical vs discretionary trade behaviour
- Monte Carlo pass / fail simulation
- Recommendation engine for different trader styles

## `app.py`

Contains the Streamlit UI:

- Sidebar controls
- Recommendation matrix
- 2x2 chart layout
- README/help viewer
- Risk style selector
- Result table and chart rendering

`app.py` imports and uses:

```python
from prop_simulator import run_simulation, simulate_one_path
```

The Streamlit app updates the global settings inside `prop_simulator.py` before every simulation run.

---

# Account Model

The simulator currently models a typical Apex-style 50k evaluation account:

- Profit Target: `$3,000`
- Trailing Drawdown Limit: `$2,000`
- Dynamic trailing floor that moves higher whenever a new equity high is reached

A simulation ends when either:

- Equity reaches the profit target → PASS
- Equity falls below the trailing drawdown floor → FAIL
- Maximum trades reached without hitting either outcome

---

# Core Inputs

The following settings are configurable from the Streamlit sidebar or directly in `prop_simulator.py`:

```python
profit_target = 3000
dd_limit = 2000
win_rate = 0.60
profit_factor = 1.6
fixed_risk_amount = 250
strategy_mode = "Mechanical"
be_trade_percent = 20
trader_style = "Balanced"
```

## Variable Definitions

- `profit_target` → challenge profit target
- `dd_limit` → trailing drawdown distance
- `win_rate` → base win probability before streak adjustments
- `profit_factor` → reward:risk multiple of a winning trade
- `fixed_risk_amount` → user's own risk per trade for charts 1 and 2
- `strategy_mode` → `Mechanical` or `Discretionary`
- `be_trade_percent` → percentage of trades that become breakeven in discretionary mode
- `trader_style` → selected recommendation profile (`Aggressive`, `Balanced`, `Conservative`)

Example:

- Risk = `$250`
- Profit Factor = `1.6`
- Winning trade = `+$400`
- Losing trade = `-$250`

---

# Trading Modes Shown In The App

The simulator always shows four approaches:

## 1. Your Fixed Risk

Uses the user's chosen fixed risk amount on every trade.

Example:

- Risk `$250` every trade

## 2. Your Dynamic Risk

Uses the user's chosen risk while at a new equity high.

If the account drops below the previous peak, risk is automatically cut in half.

Example:

- Risk `$250` at highs
- Risk `$125` while in drawdown

## 3. Recommended Style

Chart 3 changes depending on the selected Recommendation Style in Streamlit:

- Aggressive Recommended
- Balanced Recommended
- Conservative Recommended

The recommended risk size is generated automatically and is independent from the user's own fixed risk amount.

## 4. Fastest Safe

Searches across a wider range of risk sizes and finds the fastest way to pass while still maintaining acceptable odds.

---

# Recommendation Styles

The simulator includes three recommendation profiles.

These profiles only affect the recommended sizing engine — they do NOT change the user's own Fixed / Dynamic charts.

| Style | Target Pass Rate | Typical Risk Range | Behaviour |
|---|---:|---:|---|
| Aggressive | 50–75% | ~35–60% of DD | Prioritises speed and accepts higher blow-up risk |
| Balanced | 75–90% | ~20–35% of DD | Middle ground between speed and safety |
| Conservative | 90–100% | ~10–20% of DD | Prioritises survival and lowest blow-up probability |

For a `$2,000` trailing drawdown account, typical recommendation ranges are:

- Aggressive ≈ `$700–1200`
- Balanced ≈ `$400–700`
- Conservative ≈ `$200–400`

The recommendation matrix in the app compares:

- Your Fixed Risk
- Your Dynamic Risk
- Aggressive Recommended
- Balanced Recommended
- Conservative Recommended
- Fastest Safe

---

# Mechanical vs Discretionary Mode

## Mechanical Mode

Every trade is either:

- Full winner = `profit_factor × risk`
- Full loser = `-1 × risk`

Example:

- Win Rate = `60%`
- Profit Factor = `1.6`
- Risk = `$250`

Then:

- Win = `+$400`
- Loss = `-$250`

Mechanical mode still includes:

- Hot streaks
- Cold streaks
- No-trade periods

The only difference is that every executed trade resolves as a full win or full loss.

## Discretionary Mode

Discretionary mode allows a percentage of trades to become breakeven scratches.

Example:

```python
be_trade_percent = 20
```

Means approximately 20% of trades produce `0R` instead of a win or loss.

This better reflects:

- Partial exits
- Breakeven management
- Manual trade management
- Runner-based systems

---

# Streak Model

The simulator does NOT assume every trade is independent.

Instead it models realistic clusters of wins and losses.

## Hot Streaks

Occasionally performance temporarily improves.

Default behaviour:

- ~4% chance to start
- Win rate increases by about `+18%`
- Average length ≈ 4 trades

## Cold Streaks

Cold streaks are more common than hot streaks.

Default behaviour:

- ~8% chance to start
- Win rate decreases by about `-22%`
- Average length ≈ 6 trades

## No-Trade Periods

The simulator also includes quiet periods with no valid setup.

Default:

- ~22% chance of a no-trade step

This creates more realistic equity curves and more realistic time-to-pass estimates.

---

# Trailing Drawdown Logic

Trailing drawdown is tracked exactly as in the prop challenge:

```text
trailing_floor = highest_equity - dd_limit
```

The floor only moves higher when equity makes a new high.

Example:

| Equity Peak | Trailing Floor |
|---|---:|
| $0 | -$2,000 |
| $500 | -$1,500 |
| $1,500 | -$500 |
| $3,000 | +$1,000 |

The dashed line shown on every chart is this trailing drawdown floor.

---

# Recommendation Engine Logic

The recommendation engine tests many different risk sizes.

Typical search ranges:

- Conservative → 10–20% of DD
- Balanced → 20–35% of DD
- Aggressive → 35–60% of DD
- Fastest Safe → up to 100% of DD

Each style uses a different scoring function:

- Conservative heavily rewards pass rate and punishes blow-up risk
- Balanced rewards pass rate while also reducing average trades
- Aggressive strongly rewards fewer trades and larger risk sizes
- Fastest Safe simply finds the quickest acceptable route to pass

---

# Streamlit Features

The Streamlit app currently includes:

- Sidebar controls for all parameters
- Recommendation Style selector
- Mechanical vs Discretionary selector
- Optional breakeven percentage
- Recommendation Matrix table
- Four charts in a 2x2 layout
- Example equity curves and trailing floors
- README / Help checkbox in the sidebar

---

# Running The Project

## Python Script

```bash
python prop_simulator.py
```

## Streamlit App

```bash
streamlit run app.py
```

---

# Future Enhancements Planned

Potential next improvements:

- Target number of days to pass
- Trades per day modelling
- CSV trade-history upload
- Auto-calculation of true win rate / BE % / profit factor
- Risk-of-ruin diagnostics
- Consecutive losing streak probabilities
- Histogram of trades needed to pass
- Psychological difficulty / stress score
- Saved trader profiles