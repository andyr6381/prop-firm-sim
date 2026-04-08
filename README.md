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
```