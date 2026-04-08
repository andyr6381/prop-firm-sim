import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Prop Firm Simulator", layout="wide")
st.title("🚀 Prop Firm Challenge Monte Carlo Simulator")
st.markdown("### Test your edge with Fixed vs Dynamic risk + Smart Recommendations")

# ================== SIDEBAR INPUTS ==================
st.sidebar.header("Simulation Parameters")

profit_target = st.sidebar.number_input("Profit Target ($)", value=3000, step=100)
dd_limit = st.sidebar.number_input("Trailing Drawdown Limit ($)", value=2000, step=100)
win_rate = st.sidebar.slider("Win Rate (%)", 40, 90, 60) / 100.0
profit_factor = st.sidebar.slider("Reward : Risk Multiple", 1.0, 3.0, 1.6, 0.1)

strategy_mode = st.sidebar.radio(
    "System Type",
    ["Mechanical", "Discretionary"],
    index=0
)

if strategy_mode == "Discretionary":
    be_trade_percent = st.sidebar.slider("Breakeven Trades (%)", 0, 50, 20)
else:
    be_trade_percent = 0

fixed_risk_amount = st.sidebar.number_input("Fixed Risk Amount ($)", value=250, step=25)
num_sims = st.sidebar.slider("Number of Simulations", 1000, 10000, 3000, step=500)

# Calculate expectancy
avg_loss_r = 1.0
avg_win_r = profit_factor

if strategy_mode == "Mechanical":
    expected_r = (win_rate * avg_win_r) - ((1 - win_rate) * avg_loss_r)
else:
    effective_trade_rate = 1 - (be_trade_percent / 100)
    expected_r = effective_trade_rate * (
        (win_rate * avg_win_r) - ((1 - win_rate) * avg_loss_r)
    )

st.sidebar.metric("System Expectancy", f"{expected_r:.2f}R per trade")

if strategy_mode == "Mechanical":
    st.sidebar.caption(
        f"Risk ${fixed_risk_amount} → Win ${fixed_risk_amount * profit_factor:.0f} / Loss -${fixed_risk_amount}"
    )
else:
    st.sidebar.caption(
        f"{be_trade_percent}% of trades become breakeven. Remaining trades still use {profit_factor:.1f}R winners and -1R losses."
    )

# ================== SIMULATION FUNCTIONS ==================
@st.cache_data
def simulate_one_path(risk_dollars, dynamic=False, seed=None, return_result=False):
    rng = np.random.default_rng(seed)

    equity = 0.0
    peak = 0.0
    equities = [equity]
    breach_floors = [-dd_limit]

    current_state = "normal"
    streak_remaining = 0

    no_trade_prob = 0.22
    hot_start_prob = 0.04
    cold_start_prob = 0.08

    hot_shift = 0.18
    cold_shift = -0.22

    hot_continue_prob = 0.75
    cold_continue_prob = 0.83

    for _ in range(300):

        # Quiet / no-trade day
        if rng.random() < no_trade_prob:
            equities.append(equity)
            breach_floors.append(peak - dd_limit)
            continue

        # Start a new streak when not already in one
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

        # Mechanical vs discretionary system
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
        equity += pnl
        peak = max(peak, equity)

        equities.append(equity)
        breach_floors.append(peak - dd_limit)

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

def run_simulation(risk_dollars, dynamic=False, num_sims=2000):
    passes = 0
    blows = 0
    trades_to_pass = []
    
    for _ in range(num_sims):
        equity = 0.0
        peak = 0.0
        trade_count = 0
        current_risk = risk_dollars
        
        while trade_count < 300:
            trade_count += 1

            # Quiet / no-trade day
            if np.random.rand() < 0.22:
                continue

            # Hot / cold streak regime
            roll = np.random.rand()
            if roll < 0.04:
                p_win = min(0.95, win_rate + 0.18)
            elif roll < 0.12:
                p_win = max(0.05, win_rate - 0.22)
            else:
                p_win = win_rate

            # Mechanical vs discretionary system
            if strategy_mode == "Discretionary" and np.random.rand() < (be_trade_percent / 100):
                pnl_r = 0.0
            else:
                win = np.random.rand() < p_win
                pnl_r = avg_win_r if win else -avg_loss_r
            
            if dynamic and equity < peak:
                current_risk = risk_dollars * 0.5
            else:
                current_risk = risk_dollars
            
            pnl = current_risk * pnl_r
            equity += pnl
            peak = max(peak, equity)
            
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
            else:
                blows += 1
    
    avg_trades = round(np.mean(trades_to_pass), 1) if trades_to_pass else 300
    return {
        'pass_rate': round(passes / num_sims * 100, 1),
        'blow_rate': round(blows / num_sims * 100, 1),
        'avg_trades': avg_trades
    }

# ================== RUN BUTTON ==================
if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
    with st.spinner("Running thousands of simulations... This may take a few seconds"):
        
        fixed_stats = run_simulation(fixed_risk_amount, dynamic=False, num_sims=num_sims)
        dynamic_stats = run_simulation(fixed_risk_amount, dynamic=True, num_sims=num_sims)
        
        # Run safest + fastest-safe recommendations
        best_score = -999
        recommended_risk = 200
        recommended_stats = None

        fastest_score = -999
        fastest_risk = 200
        fastest_stats = None

        min_risk = max(50, int(dd_limit * 0.05))
        max_risk = int(dd_limit * 0.25)

        for risk in range(min_risk, max_risk + 25, 25):
            stats = run_simulation(risk, dynamic=True, num_sims=2000)

            # Safest overall recommendation
            score = (
                stats['pass_rate'] * 2
                - stats['blow_rate'] * 3
                - stats['avg_trades'] * 0.5
            )

            if score > best_score:
                best_score = score
                recommended_risk = risk
                recommended_stats = stats

            # Fastest reasonable way to pass
            if stats['pass_rate'] >= 60 and stats['blow_rate'] <= 40:
                fast_score = -stats['avg_trades']
                fast_score += stats['pass_rate'] * 0.1
                fast_score -= stats['blow_rate'] * 0.05

                if fast_score > fastest_score:
                    fastest_score = fast_score
                    fastest_risk = risk
                    fastest_stats = stats

        if recommended_stats is None:
            recommended_stats = {'pass_rate': 0, 'blow_rate': 100, 'avg_trades': 300}

        if fastest_stats is None:
            fastest_risk = recommended_risk
            fastest_stats = recommended_stats

        # ================== DISPLAY RESULTS ==================
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.subheader(f"Fixed ${fixed_risk_amount}")
            st.metric("Pass Rate", f"{fixed_stats['pass_rate']}%")
            st.metric("Blow Rate", f"{fixed_stats['blow_rate']}%")
            st.metric("Avg Trades", fixed_stats['avg_trades'])
        
        with col2:
            st.subheader(f"Dynamic ${fixed_risk_amount}")
            st.metric("Pass Rate", f"{dynamic_stats['pass_rate']}%")
            st.metric("Blow Rate", f"{dynamic_stats['blow_rate']}%")
            st.metric("Avg Trades", dynamic_stats['avg_trades'])
        
        with col3:
            st.subheader("Safest")
            st.metric("Risk Size", f"${recommended_risk}")
            st.metric("Pass Rate", f"{recommended_stats['pass_rate']}%")
            st.metric("Blow Rate", f"{recommended_stats['blow_rate']}%")
            st.metric("Avg Trades", recommended_stats['avg_trades'])

        with col4:
            st.subheader("Fastest Safe")
            st.metric("Risk Size", f"${fastest_risk}")
            st.metric("Pass Rate", f"{fastest_stats['pass_rate']}%")
            st.metric("Blow Rate", f"{fastest_stats['blow_rate']}%")
            st.metric("Avg Trades", fastest_stats['avg_trades'])

        st.success("Simulation Complete!")

        # ================== CHARTS ==================
        fig, axs = plt.subplots(2, 2, figsize=(16, 12))
        axs = axs.flatten()

        def add_stats_box(ax, stats):
            text = (
                f"Pass Rate: {stats['pass_rate']}%\n"
                f"Blow Rate: {stats['blow_rate']}%\n"
                f"Avg Trades: {stats['avg_trades']}"
            )
            ax.text(
                0.98,
                0.02,
                text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment='bottom',
                horizontalalignment='right',
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    facecolor='white',
                    edgecolor='black',
                    alpha=0.9
                )
            )

        # 1. Fixed
        for i in range(3):
            path, floor = simulate_one_path(
                fixed_risk_amount,
                dynamic=False,
                seed=100 + i
            )
            color = plt.cm.tab10(i)
            axs[0].plot(path, color=color, linewidth=2, alpha=0.9)
            axs[0].plot(floor, color=color, linestyle='--', alpha=0.5)
        axs[0].axhline(y=profit_target, color='green', linewidth=2)
        axs[0].set_title(f"1. FIXED ${fixed_risk_amount} Risk (Your Current Style)")
        axs[0].grid(True, alpha=0.3)
        add_stats_box(axs[0], fixed_stats)

        # 2. Dynamic
        for i in range(3):
            path, floor = simulate_one_path(
                fixed_risk_amount,
                dynamic=True,
                seed=200 + i
            )
            color = plt.cm.tab10(i)
            axs[1].plot(path, color=color, linewidth=2, alpha=0.9)
            axs[1].plot(floor, color=color, linestyle='--', alpha=0.5)
        axs[1].axhline(y=profit_target, color='green', linewidth=2)
        axs[1].set_title(f"2. DYNAMIC ${fixed_risk_amount} Risk (halve in drawdown)")
        axs[1].grid(True, alpha=0.3)
        add_stats_box(axs[1], dynamic_stats)

        # 3. Safest Recommendation
        shown = 0
        seed = recommended_risk * 10
        while shown < 3:
            path, floor, result = simulate_one_path(
                recommended_risk,
                dynamic=True,
                seed=seed,
                return_result=True
            )
            if result == 'pass':
                color = plt.cm.tab10(shown)
                axs[2].plot(path, color=color, linewidth=2, alpha=0.9)
                axs[2].plot(floor, color=color, linestyle='--', alpha=0.5)
                shown += 1
            seed += 1

        axs[2].axhline(y=profit_target, color='green', linewidth=2)
        axs[2].set_title(
            f"3. SAFEST: Dynamic ${recommended_risk} Risk (halve in drawdown)"
        )
        axs[2].grid(True, alpha=0.3)
        add_stats_box(axs[2], recommended_stats)

        # 4. Fastest Safe
        shown = 0
        seed = fastest_risk * 20
        while shown < 3:
            path, floor, result = simulate_one_path(
                fastest_risk,
                dynamic=True,
                seed=seed,
                return_result=True
            )
            if result == 'pass':
                color = plt.cm.tab10(shown)
                axs[3].plot(path, color=color, linewidth=2, alpha=0.9)
                axs[3].plot(floor, color=color, linestyle='--', alpha=0.5)
                shown += 1
            seed += 1

        axs[3].axhline(y=profit_target, color='green', linewidth=2)
        axs[3].set_title(
            f"4. FASTEST SAFE: Dynamic ${fastest_risk} Risk (halve in drawdown)"
        )
        axs[3].grid(True, alpha=0.3)
        add_stats_box(axs[3], fastest_stats)

        plt.tight_layout()
        st.pyplot(fig)

else:
    st.info("👈 Adjust the settings in the sidebar and click **Run Simulation** to start.")

st.caption("Built with Streamlit • Monte Carlo Prop Firm Simulator")