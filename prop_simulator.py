import numpy as np
import matplotlib.pyplot as plt

# ================== USER SETTINGS =================
profit_target = 8000
dd_limit = 2000
win_rate = 0.6
profit_factor = 1.6
fixed_risk_amount = 250   # ← Change this freely
consistency_limit_percent = 20   # 0 disables. Example: 20 = max 20% of target profit per winning trade

strategy_mode = "Mechanical"   # "Mechanical" or "Discretionary"
be_trade_percent = 20           # Only used in Discretionary mode

max_trades = 300
num_sims = 2000

 # profit_factor here represents the average reward:risk multiple of a winning trade
# e.g. 1.5 means risk $250 to make $375
avg_loss_r = 1.0
avg_win_r = profit_factor

# Optional prop-firm consistency rule.
# Example: target $3000 and limit 20% = max $600 profit per winning trade.
consistency_cap_amount = (
    profit_target * (consistency_limit_percent / 100)
    if consistency_limit_percent > 0
    else None
)

# Calculate and display system expectancy in R
if strategy_mode == "Mechanical":
    expected_r = (win_rate * avg_win_r) - ((1 - win_rate) * avg_loss_r)
else:
    effective_trade_rate = 1 - (be_trade_percent / 100)
    expected_r = (
        effective_trade_rate
        * ((win_rate * avg_win_r) - ((1 - win_rate) * avg_loss_r))
    )

print(f"System Type: {strategy_mode}")
if strategy_mode == "Discretionary":
    print(f"Breakeven Trades: {be_trade_percent}%")
print(f"System Expectancy: {expected_r:.2f}R per trade")
if consistency_cap_amount is not None:
    print(
        f"Consistency Rule Enabled: Max ${consistency_cap_amount:.0f} per winning trade "
        f"({consistency_limit_percent}% of target)"
    )

def simulate_one_path(
    risk_dollars,
    dynamic=False,
    seed=None,
    consistency_cap=None,
    return_result=False
):
    rng = np.random.default_rng(seed)

    equity = 0.0
    peak = 0.0
    equities = [equity]
    breach_floors = [-dd_limit]

    # --- Streak state ---
    current_state = "normal"   # one of: normal, hot, cold
    streak_remaining = 0

    # --- Suggested default streak parameters ---
    no_trade_prob = 0.22

    hot_start_prob = 0.04       # hot streaks are uncommon
    cold_start_prob = 0.08      # cold streaks are more common than hot

    hot_shift = 0.18            # +18% win rate during hot streaks
    cold_shift = -0.22          # -22% win rate during cold streaks

    # Geometric-style durations:
    # average hot streak ≈ 4 trades, average cold streak ≈ 6 trades
    hot_continue_prob = 0.75
    cold_continue_prob = 0.83

    for _ in range(max_trades):

        # -----------------------------------------------------------
        # Occasionally skip a trade entirely to simulate quiet sessions,
        # indecision, no setup, or low-quality market conditions.
        # -----------------------------------------------------------
        if rng.random() < no_trade_prob:
            equities.append(equity)
            breach_floors.append(peak - dd_limit)
            continue

        # -----------------------------------------------------------
        # If not already in a streak, occasionally enter a new one.
        # Cold streaks are deliberately more common than hot streaks.
        # -----------------------------------------------------------
        if streak_remaining <= 0:
            current_state = "normal"

            roll = rng.random()
            if roll < hot_start_prob:
                current_state = "hot"
                streak_remaining = 1
                while rng.random() < hot_continue_prob:
                    streak_remaining += 1

            elif roll < hot_start_prob + cold_start_prob:
                current_state = "cold"
                streak_remaining = 1
                while rng.random() < cold_continue_prob:
                    streak_remaining += 1

        # -----------------------------------------------------------
        # Adjust the temporary win rate based on the current streak.
        # Clamp so it always stays within a realistic range.
        # -----------------------------------------------------------
        if current_state == "hot":
            p_win = min(0.95, win_rate + hot_shift)
        elif current_state == "cold":
            p_win = max(0.05, win_rate + cold_shift)
        else:
            p_win = win_rate

        # Use one trade from the current streak.
        if streak_remaining > 0:
            streak_remaining -= 1
            if streak_remaining == 0:
                current_state = "normal"

        # -----------------------------------------------------------
        # Mechanical mode: normal binary win/loss.
        # Discretionary mode: some trades become breakeven scratches.
        # -----------------------------------------------------------
        if strategy_mode == "Discretionary" and rng.random() < (be_trade_percent / 100):
            pnl_r = 0.0
        else:
            win = rng.random() < p_win
            pnl_r = avg_win_r if win else -avg_loss_r

        if dynamic and equity < peak:
            current_risk = risk_dollars * 0.5
        else:
            current_risk = risk_dollars

        pnl = current_risk * pnl_r

        # Apply optional consistency cap to profitable trades.
        if consistency_cap is not None and pnl > 0:
            pnl = min(pnl, consistency_cap)
        elif consistency_cap is None and consistency_cap_amount is not None and pnl > 0:
            pnl = min(pnl, consistency_cap_amount)

        equity += pnl
        peak = max(peak, equity)

        equities.append(equity)
        breach_floors.append(peak - dd_limit)

        # Trailing drawdown logic remains unchanged.
        if equity < peak - dd_limit:
            for _ in range(5):
                equities.append(equity)
                breach_floors.append(peak - dd_limit)
            break

        if equity >= profit_target:
            break

    result = 'pass' if equity >= profit_target else 'blow'

    if return_result:
        return np.array(equities), np.array(breach_floors), result

    return np.array(equities), np.array(breach_floors)

def run_simulation(
    risk_dollars,
    dynamic=False,
    num_sims=1500,
    consistency_cap=None
):
    passes = 0
    blows = 0
    trades_to_pass = []

    for sim in range(num_sims):
        rng = np.random.default_rng(sim)

        equity = 0.0
        peak = 0.0
        trade_count = 0

        current_state = "normal"
        streak_remaining = 0

        no_trade_prob = 0.22
        hot_start_prob = 0.04
        cold_start_prob = 0.08

        hot_shift = 0.18
        cold_shift = -0.22

        hot_continue_prob = 0.75
        cold_continue_prob = 0.83

        while trade_count < max_trades:

            # Quiet / no-trade period
            if rng.random() < no_trade_prob:
                trade_count += 1
                continue

            # Start new streak if not already in one
            if streak_remaining <= 0:
                current_state = "normal"

                roll = rng.random()
                if roll < hot_start_prob:
                    current_state = "hot"
                    streak_remaining = 1
                    while rng.random() < hot_continue_prob:
                        streak_remaining += 1

                elif roll < hot_start_prob + cold_start_prob:
                    current_state = "cold"
                    streak_remaining = 1
                    while rng.random() < cold_continue_prob:
                        streak_remaining += 1

            # Temporary win-rate adjustment
            if current_state == "hot":
                p_win = min(0.95, win_rate + hot_shift)
            elif current_state == "cold":
                p_win = max(0.05, win_rate + cold_shift)
            else:
                p_win = win_rate

            if streak_remaining > 0:
                streak_remaining -= 1
                if streak_remaining == 0:
                    current_state = "normal"

            # Mechanical vs discretionary mode
            if strategy_mode == "Discretionary" and rng.random() < (be_trade_percent / 100):
                pnl_r = 0.0
            else:
                win = rng.random() < p_win
                pnl_r = avg_win_r if win else -avg_loss_r

            if dynamic and equity < peak:
                current_risk = risk_dollars * 0.5
            else:
                current_risk = risk_dollars

            pnl = current_risk * pnl_r

            # Apply optional consistency cap to profitable trades.
            if consistency_cap is not None and pnl > 0:
                pnl = min(pnl, consistency_cap)
            elif consistency_cap is None and consistency_cap_amount is not None and pnl > 0:
                pnl = min(pnl, consistency_cap_amount)

            equity += pnl
            peak = max(peak, equity)

            trade_count += 1

            if equity < peak - dd_limit:
                blows += 1
                break

            if equity >= profit_target:
                passes += 1
                trades_to_pass.append(trade_count)
                break

        else:
            if equity >= profit_target:
                passes += 1
                trades_to_pass.append(trade_count)
            else:
                blows += 1

    avg_trades = round(np.mean(trades_to_pass), 1) if trades_to_pass else max_trades

    return {
        'pass_rate': round(passes / num_sims * 100, 1),
        'blow_rate': round(blows / num_sims * 100, 1),
        'avg_trades': avg_trades
    }

# ================== FIND RECOMMENDED ==================
print("Finding optimal risk...\n")
print(f"Testing risk sizes from ${min_risk if 'min_risk' in locals() else int(dd_limit * 0.05)} to ${int(dd_limit * 0.25)} in $25 increments")

best_score = -999
recommended_risk = 200
recommended_dynamic = True
recommended_stats = None

fastest_score = -999
fastest_risk = 200
fastest_dynamic = True
fastest_stats = None

min_risk = max(50, int(dd_limit * 0.05))

# Standard recommendation search remains conservative.
max_risk = int(dd_limit * 0.25)

# Allow the "Fastest Safe" route to test up to the full drawdown limit.
# This means on a $2000 trailing DD account it can evaluate risk sizes up to $2000.
fastest_max_risk = int(dd_limit)

risk_step = 25

risk_sizes = list(range(min_risk, fastest_max_risk + risk_step, risk_step))

for risk in risk_sizes:
    stats = run_simulation(risk, dynamic=True, num_sims=2000)

    print(
        f"${risk}: Pass {stats['pass_rate']}% | "
        f"Blow {stats['blow_rate']}% | "
        f"Avg Trades {stats['avg_trades']}"
    )

    # Prioritize higher pass rate, lower blow rate, but also penalize
    # setups that require too many trades to finish.
    score = (
        stats['pass_rate'] * 2
        - stats['blow_rate'] * 3
        - stats['avg_trades'] * 0.5
    )

    # Keep the main recommendation conservative by only considering
    # risk sizes up to the original 25% of drawdown limit.
    if risk <= max_risk and score > best_score:
        best_score = score
        recommended_risk = risk
        recommended_dynamic = True
        recommended_stats = stats

    # Separate "fastest safe" recommendation.
    # First require the setup to still be reasonably safe.
    # Then choose the one that reaches the target in the fewest trades.
    if stats['pass_rate'] >= 60 and stats['blow_rate'] <= 40:
        fast_score = -stats['avg_trades']

        # If two risk sizes have similar speed, prefer the safer one.
        fast_score += stats['pass_rate'] * 0.1
        fast_score -= stats['blow_rate'] * 0.05

        if fast_score > fastest_score:
            fastest_score = fast_score
            fastest_risk = risk
            fastest_dynamic = True
            fastest_stats = stats

if recommended_stats is None:
    recommended_stats = {'pass_rate': 0, 'blow_rate': 100, 'avg_trades': max_trades}

if fastest_stats is None:
    fastest_stats = {'pass_rate': 0, 'blow_rate': 100, 'avg_trades': max_trades}

# If nothing met the safety threshold, fall back to the highest pass-rate option.
if fastest_stats['pass_rate'] == 0:
    fastest_risk = recommended_risk
    fastest_dynamic = recommended_dynamic
    fastest_stats = recommended_stats

half_risk = recommended_risk // 2

print("=== RECOMMENDATION ===")
print(f"Best: Dynamic ${recommended_risk} → halve to ${half_risk} when in drawdown")
print(
    f"Pass Rate: {recommended_stats['pass_rate']}% | "
    f"Blow Rate: {recommended_stats['blow_rate']}% | "
    f"Avg Trades: {recommended_stats['avg_trades']}"
)

print("\n=== FASTEST SAFE OPTION ===")
print(f"Best: Dynamic ${fastest_risk} → halve to ${fastest_risk // 2} when in drawdown")
print(
    f"Pass Rate: {fastest_stats['pass_rate']}% | "
    f"Blow Rate: {fastest_stats['blow_rate']}% | "
    f"Avg Trades: {fastest_stats['avg_trades']}"
)

# ================== CHARTS ==================
fig, axs = plt.subplots(2, 2, figsize=(16, 12))
axs = axs.flatten()

def add_stats_box(ax, pass_rate, blow_rate, avg_trades=None):
    text = f"Pass Rate: {pass_rate}%\nBlow Rate: {blow_rate}%"
    if avg_trades is not None:
        text += f"\nAvg Trades: {avg_trades}"
    ax.text(
        0.98,
        0.02,
        text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='bottom',
        horizontalalignment='right',
        bbox=dict(
            boxstyle="round,pad=0.5",
            facecolor='white',
            edgecolor='black',
            alpha=0.9
        )
    )

fixed_stats = run_simulation(fixed_risk_amount, dynamic=False, num_sims=num_sims)
dynamic_stats = run_simulation(fixed_risk_amount, dynamic=True, num_sims=num_sims)

# Chart 1: Fixed
for i in range(3):
    path, floor = simulate_one_path(fixed_risk_amount, dynamic=False)
    color = plt.cm.tab10(i)
    axs[0].plot(path, color=color, linewidth=2.0, alpha=0.9, label=f'Fixed Path {i+1}')
    axs[0].plot(floor, color=color, linestyle='--', alpha=0.55)
axs[0].axhline(y=profit_target, color='green', linestyle='-', linewidth=2.5, label='Pass Target')
consistency_suffix = (
    f'Consistency Cap: ${consistency_cap_amount:.0f} ({consistency_limit_percent}%)'
    if consistency_cap_amount is not None
    else 'No Consistency Cap'
)

axs[0].set_title(
    f'1. FIXED ${fixed_risk_amount} Risk',
    fontsize=13,
    fontweight='bold',
    pad=28
)
axs[0].text(
    0.5,
    1.01,
    f'Your Current Style\n{consistency_suffix}',
    transform=axs[0].transAxes,
    ha='center',
    va='bottom',
    fontsize=10,
    fontweight='normal'
)
axs[0].set_ylabel('Profit / Loss ($)')
axs[0].legend(loc='upper left')
axs[0].grid(True, alpha=0.3)
add_stats_box(
    axs[0],
    fixed_stats['pass_rate'],
    fixed_stats['blow_rate'],
    fixed_stats['avg_trades']
)

# Chart 2: Dynamic at same risk
for i in range(3):
    path, floor = simulate_one_path(fixed_risk_amount, dynamic=True)
    color = plt.cm.tab10(i)
    axs[1].plot(path, color=color, linewidth=2.0, alpha=0.9, label=f'Dynamic Path {i+1}')
    axs[1].plot(floor, color=color, linestyle='--', alpha=0.55)
axs[1].axhline(y=profit_target, color='green', linestyle='-', linewidth=2.5, label='Pass Target')
axs[1].set_title(
    f'2. DYNAMIC ${fixed_risk_amount} Risk',
    fontsize=13,
    fontweight='bold',
    pad=28
)
axs[1].text(
    0.5,
    1.01,
    f'Rule: Halve Risk in Drawdown\n{consistency_suffix}',
    transform=axs[1].transAxes,
    ha='center',
    va='bottom',
    fontsize=10,
    fontweight='normal'
)
axs[1].set_ylabel('Profit / Loss ($)')
axs[1].legend(loc='upper left')
axs[1].grid(True, alpha=0.3)
add_stats_box(
    axs[1],
    dynamic_stats['pass_rate'],
    dynamic_stats['blow_rate'],
    dynamic_stats['avg_trades']
)

# Chart 3: Recommended
shown = 0
seed = recommended_risk * 10

while shown < 3:
    path, floor, result = simulate_one_path(
        recommended_risk,
        dynamic=recommended_dynamic,
        seed=seed,
        return_result=True
    )

    if result == 'pass':
        color = plt.cm.tab10(shown)
        axs[2].plot(path, color=color, linewidth=2.0, alpha=0.9,
                    label=f'Recommended Path {shown+1}')
        axs[2].plot(floor, color=color, linestyle='--', alpha=0.55)
        shown += 1

    seed += 1

axs[2].axhline(y=profit_target, color='green', linestyle='-', linewidth=2.5, label='Pass Target')
axs[2].set_title(
    f'3. SAFEST: Dynamic ${recommended_risk} Risk',
    fontsize=13,
    fontweight='bold',
    pad=28
)
axs[2].text(
    0.5,
    1.01,
    f'Rule: Halve to ${half_risk} in Drawdown\n{consistency_suffix}',
    transform=axs[2].transAxes,
    ha='center',
    va='bottom',
    fontsize=10,
    fontweight='normal'
)
axs[2].set_xlabel('Number of Trades')
axs[2].set_ylabel('Profit / Loss ($)')
axs[2].legend(loc='upper left')
axs[2].grid(True, alpha=0.3)
add_stats_box(
    axs[2],
    recommended_stats['pass_rate'],
    recommended_stats['blow_rate'],
    recommended_stats['avg_trades']
)

# Chart 4: Fastest Safe
shown = 0
seed = fastest_risk * 20

while shown < 3:
    path, floor, result = simulate_one_path(
        fastest_risk,
        dynamic=fastest_dynamic,
        seed=seed,
        return_result=True
    )

    if result == 'pass':
        color = plt.cm.tab10(shown)
        axs[3].plot(
            path,
            color=color,
            linewidth=2.0,
            alpha=0.9,
            label=f'Fast Path {shown+1}'
        )
        axs[3].plot(floor, color=color, linestyle='--', alpha=0.55)
        shown += 1

    seed += 1

axs[3].axhline(y=profit_target, color='green', linestyle='-', linewidth=2.5, label='Pass Target')
axs[3].set_title(
    f'4. FASTEST SAFE: Dynamic ${fastest_risk} Risk',
    fontsize=13,
    fontweight='bold',
    pad=28
)
axs[3].text(
    0.5,
    1.01,
    f'Rule: Halve to ${fastest_risk // 2} in Drawdown\n{consistency_suffix}',
    transform=axs[3].transAxes,
    ha='center',
    va='bottom',
    fontsize=10,
    fontweight='normal'
)
axs[3].set_xlabel('Number of Trades')
axs[3].set_ylabel('Profit / Loss ($)')
axs[3].legend(loc='upper left')
axs[3].grid(True, alpha=0.3)
add_stats_box(
    axs[3],
    fastest_stats['pass_rate'],
    fastest_stats['blow_rate'],
    fastest_stats['avg_trades']
)

plt.tight_layout()
plt.show()