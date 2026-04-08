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