import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os
import webbrowser

import prop_simulator
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

# ===== Trader Style selector =====
trader_style = st.sidebar.radio(
    "Recommendation Style",
    ["Aggressive", "Balanced", "Conservative"],
    index=1,
    help=(
        "Aggressive = prioritize speed and accept lower pass probability.\n"
        "Balanced = middle ground.\n"
        "Conservative = prioritize account survival and 90%+ pass odds."
    )
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
        
        # Sync Streamlit sidebar values into the simulator engine
        prop_simulator.profit_target = profit_target
        prop_simulator.dd_limit = dd_limit
        prop_simulator.win_rate = win_rate
        prop_simulator.profit_factor = profit_factor
        prop_simulator.avg_win_r = profit_factor
        prop_simulator.avg_loss_r = 1.0
        prop_simulator.strategy_mode = strategy_mode
        prop_simulator.be_trade_percent = be_trade_percent
        prop_simulator.trader_style = trader_style
        
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
        
        def get_style_recommendation(style_name):
            if style_name == "Aggressive":
                min_required_pass_rate = 50
            elif style_name == "Conservative":
                min_required_pass_rate = 90
            else:
                min_required_pass_rate = 75

            best_score = -999
            best_risk = None
            best_stats = None

            for risk in range(min_risk, max_risk + risk_step, risk_step):
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

                if (
                    stats['pass_rate'] >= min_required_pass_rate
                    and score > best_score
                ):
                    best_score = score
                    best_risk = risk
                    best_stats = stats

            return best_risk, best_stats

        # Recommendation logic based on selected recommendation style
        min_risk = max(50, int(dd_limit * 0.05))
        max_risk = int(dd_limit * 0.25)
        fastest_max_risk = int(dd_limit)
        risk_step = 25

        aggressive_risk, aggressive_stats = get_style_recommendation("Aggressive")
        balanced_risk, balanced_stats = get_style_recommendation("Balanced")
        conservative_risk, conservative_stats = get_style_recommendation("Conservative")

        if trader_style == "Aggressive":
            recommended_risk = aggressive_risk
            recommended_stats = aggressive_stats
            style_description = "Prioritizes speed and accepts lower pass probability"
        elif trader_style == "Conservative":
            recommended_risk = conservative_risk
            recommended_stats = conservative_stats
            style_description = "Prioritizes survival and 90%+ pass probability"
        else:
            recommended_risk = balanced_risk
            recommended_stats = balanced_stats
            style_description = "Balanced between speed and account protection"

        st.info(
            f"Recommendation Style: {trader_style} — {style_description}. "
            f"Chart 3 shows this recommendation."
        )

        # Fallback if no recommendation meets the criteria
        if recommended_stats is None:
            recommended_risk = fixed_risk_amount
            recommended_stats = dynamic_stats

        # Fastest safe recommendation
        fastest_score = -999
        fastest_risk = fixed_risk_amount
        fastest_stats = dynamic_stats

        for risk in range(min_risk, fastest_max_risk + risk_step, risk_step):
            stats = run_simulation(
                risk,
                dynamic=True,
                num_sims=2000,
                consistency_cap=consistency_cap_amount
            )

            if stats['pass_rate'] >= 60 and stats['blow_rate'] <= 40:
                fast_score = (
                    -stats['avg_trades']
                    + stats['pass_rate'] * 0.1
                    - stats['blow_rate'] * 0.05
                )

                if fast_score > fastest_score:
                    fastest_score = fast_score
                    fastest_risk = risk
                    fastest_stats = stats

        st.markdown("### Recommendation Matrix")

        matrix_rows = [
            {
                "Plan": f"Your Fixed ${fixed_risk_amount}",
                "Risk": f"${fixed_risk_amount}",
                "Pass %": fixed_stats['pass_rate'],
                "Blow %": fixed_stats['blow_rate'],
                "Avg Trades": fixed_stats['avg_trades']
            },
            {
                "Plan": f"Your Dynamic ${fixed_risk_amount}",
                "Risk": f"${fixed_risk_amount}",
                "Pass %": dynamic_stats['pass_rate'],
                "Blow %": dynamic_stats['blow_rate'],
                "Avg Trades": dynamic_stats['avg_trades']
            }
        ]

        if aggressive_stats is not None:
            matrix_rows.append({
                "Plan": "Aggressive Recommended",
                "Risk": f"${aggressive_risk}",
                "Pass %": aggressive_stats['pass_rate'],
                "Blow %": aggressive_stats['blow_rate'],
                "Avg Trades": aggressive_stats['avg_trades']
            })

        if balanced_stats is not None:
            matrix_rows.append({
                "Plan": "Balanced Recommended",
                "Risk": f"${balanced_risk}",
                "Pass %": balanced_stats['pass_rate'],
                "Blow %": balanced_stats['blow_rate'],
                "Avg Trades": balanced_stats['avg_trades']
            })

        if conservative_stats is not None:
            matrix_rows.append({
                "Plan": "Conservative Recommended",
                "Risk": f"${conservative_risk}",
                "Pass %": conservative_stats['pass_rate'],
                "Blow %": conservative_stats['blow_rate'],
                "Avg Trades": conservative_stats['avg_trades']
            })

        matrix_rows.append({
            "Plan": "Fastest Safe",
            "Risk": f"${fastest_risk}",
            "Pass %": fastest_stats['pass_rate'],
            "Blow %": fastest_stats['blow_rate'],
            "Avg Trades": fastest_stats['avg_trades']
        })

        st.dataframe(matrix_rows, use_container_width=True)



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
            f"3. {trader_style.upper()} RECOMMENDED: Dynamic ${recommended_risk} Risk",
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