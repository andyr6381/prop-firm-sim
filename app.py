import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os
import webbrowser

from prop_simulator import run_simulation, simulate_one_path

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

consistency_limit_percent = st.sidebar.slider(
    "Consistency Rule (% of Profit Target)",
    min_value=0,
    max_value=100,
    value=0,
    step=5,
    help="0 disables the rule. Example: 20 means no single winning trade can contribute more than 20% of the profit target."
)

consistency_cap_amount = (
    profit_target * (consistency_limit_percent / 100)
    if consistency_limit_percent > 0
    else None
)

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

# ================== README / HELP ==================
st.sidebar.markdown("---")
st.sidebar.subheader("Documentation")

show_readme = st.sidebar.checkbox("📖 Show README")


if show_readme:
    st.markdown("# README / Help")

    readme_path = os.path.join(os.path.dirname(__file__), "README.md")

    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()

        st.markdown(readme_text)
    else:
        st.error("README.md file not found in the app folder.")

    st.stop()

# ================== REST OF YOUR APP ==================
if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
    with st.spinner("Running thousands of simulations... This may take a few seconds"):
        
        fixed_stats = run_simulation(
            fixed_risk_amount,
            dynamic=False,
            num_sims=num_sims,
            consistency_cap=consistency_cap_amount
        )
        dynamic_stats = run_simulation(
            fixed_risk_amount,
            dynamic=True,
            num_sims=num_sims,
            consistency_cap=consistency_cap_amount
        )
        
        # Recommendation logic (simplified)
        best_score = -999
        recommended_risk = 200
        recommended_stats = None

        fastest_score = -999
        fastest_risk = 200
        fastest_stats = None

        min_risk = max(50, int(dd_limit * 0.05))

        # Conservative cap for the "Safest" recommendation
        max_risk = int(dd_limit * 0.25)

        # Allow the "Fastest Safe" route to evaluate all the way up to
        # the full trailing drawdown limit.
        fastest_max_risk = int(dd_limit)

        risk_step = 25

        for risk in range(min_risk, fastest_max_risk + risk_step, risk_step):
            stats = run_simulation(
                risk,
                dynamic=True,
                num_sims=2000,
                consistency_cap=consistency_cap_amount
            )

            score = (
                stats['pass_rate'] * 2
                - stats['blow_rate'] * 3
                - stats['avg_trades'] * 0.5
            )

            # Keep the main recommendation conservative.
            if risk <= max_risk and score > best_score:
                best_score = score
                recommended_risk = risk
                recommended_stats = stats

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

        # Display Results
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.subheader("Fixed")
            st.metric("Risk Size", f"${fixed_risk_amount}")
            st.metric("Pass Rate", f"{fixed_stats['pass_rate']}%")
            st.metric("Blow Rate", f"{fixed_stats['blow_rate']}%")
            st.metric("Avg Trades", fixed_stats['avg_trades'])
        
        with col2:
            st.subheader("Dynamic")
            st.metric("Risk Size", f"${fixed_risk_amount}")
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


        # ================== CHARTS ==================
        fig, axs = plt.subplots(2, 2, figsize=(16, 12))
        axs = axs.flatten()

        consistency_suffix = (
            f"Consistency Cap: ${consistency_cap_amount:.0f} ({consistency_limit_percent}%)"
            if consistency_cap_amount is not None
            else "No Consistency Cap"
        )

        def add_stats_box(ax, risk, stats):
            text = (
                f"Risk: ${risk}\n"
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
        shown = 0
        seed = 100
        while shown < 3:
            path, floor, result = simulate_one_path(
                fixed_risk_amount,
                dynamic=False,
                seed=seed,
                consistency_cap=consistency_cap_amount,
                return_result=True
            )

            if fixed_stats['pass_rate'] > 50:
                should_show = result == 'pass'
            else:
                should_show = True

            if should_show:
                color = plt.cm.tab10(shown)
                axs[0].plot(path, color=color, linewidth=2)
                axs[0].plot(floor, color=color, linestyle='--', alpha=0.5)
                shown += 1

            seed += 1

        axs[0].axhline(y=profit_target, color='green', linewidth=2)
        axs[0].set_title(
            f"1. FIXED ${fixed_risk_amount} Risk",
            fontsize=13,
            fontweight='bold',
            pad=28
        )
        axs[0].text(
            0.5,
            1.01,
            f"Your Current Style\n{consistency_suffix}",
            transform=axs[0].transAxes,
            ha='center',
            va='bottom',
            fontsize=10
        )
        axs[0].grid(True, alpha=0.3)
        add_stats_box(axs[0], fixed_risk_amount, fixed_stats)

        # 2. Dynamic
        shown = 0
        seed = 200
        while shown < 3:
            path, floor, result = simulate_one_path(
                fixed_risk_amount,
                dynamic=True,
                seed=seed,
                consistency_cap=consistency_cap_amount,
                return_result=True
            )

            if dynamic_stats['pass_rate'] > 50:
                should_show = result == 'pass'
            else:
                should_show = True

            if should_show:
                color = plt.cm.tab10(shown)
                axs[1].plot(path, color=color, linewidth=2)
                axs[1].plot(floor, color=color, linestyle='--', alpha=0.5)
                shown += 1

            seed += 1

        axs[1].axhline(y=profit_target, color='green', linewidth=2)
        axs[1].set_title(
            f"2. DYNAMIC ${fixed_risk_amount} Risk",
            fontsize=13,
            fontweight='bold',
            pad=28
        )
        axs[1].text(
            0.5,
            1.01,
            f"Rule: Halve Risk in Drawdown\n{consistency_suffix}",
            transform=axs[1].transAxes,
            ha='center',
            va='bottom',
            fontsize=10
        )
        axs[1].grid(True, alpha=0.3)
        add_stats_box(axs[1], fixed_risk_amount, dynamic_stats)

        # 3. Safest
        shown = 0
        seed = recommended_risk * 10
        while shown < 3:
            path, floor, result = simulate_one_path(
                recommended_risk,
                dynamic=True,
                seed=seed,
                consistency_cap=consistency_cap_amount,
                return_result=True
            )

            if result == 'pass':
                color = plt.cm.tab10(shown)
                axs[2].plot(path, color=color, linewidth=2)
                axs[2].plot(floor, color=color, linestyle='--', alpha=0.5)
                shown += 1

            seed += 1

        axs[2].axhline(y=profit_target, color='green', linewidth=2)
        axs[2].set_title(
            f"3. SAFEST: Dynamic ${recommended_risk} Risk",
            fontsize=13,
            fontweight='bold',
            pad=28
        )
        axs[2].text(
            0.5,
            1.01,
            f"Rule: Halve to ${recommended_risk // 2} in Drawdown\n{consistency_suffix}",
            transform=axs[2].transAxes,
            ha='center',
            va='bottom',
            fontsize=10
        )
        axs[2].grid(True, alpha=0.3)
        add_stats_box(axs[2], recommended_risk, recommended_stats)

        # 4. Fastest Safe
        shown = 0
        seed = fastest_risk * 20
        while shown < 3:
            path, floor, result = simulate_one_path(
                fastest_risk,
                dynamic=True,
                seed=seed,
                consistency_cap=consistency_cap_amount,
                return_result=True
            )

            if result == 'pass':
                color = plt.cm.tab10(shown)
                axs[3].plot(path, color=color, linewidth=2)
                axs[3].plot(floor, color=color, linestyle='--', alpha=0.5)
                shown += 1

            seed += 1

        axs[3].axhline(y=profit_target, color='green', linewidth=2)
        axs[3].set_title(
            f"4. FASTEST SAFE: Dynamic ${fastest_risk} Risk",
            fontsize=13,
            fontweight='bold',
            pad=28
        )
        axs[3].text(
            0.5,
            1.01,
            f"Rule: Halve to ${fastest_risk // 2} in Drawdown\n{consistency_suffix}",
            transform=axs[3].transAxes,
            ha='center',
            va='bottom',
            fontsize=10
        )
        axs[3].grid(True, alpha=0.3)
        add_stats_box(axs[3], fastest_risk, fastest_stats)

        plt.tight_layout()
        st.pyplot(fig)

        st.success("Simulation Complete!")

else:
    st.info("👈 Adjust the settings in the sidebar and click **Run Simulation** to start.")

st.caption("Built with Streamlit • Monte Carlo Prop Firm Simulator")

# If simulate_one_path is used elsewhere in this file, ensure it's imported:
# from prop_simulator import simulate_one_path