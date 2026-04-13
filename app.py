import os

import matplotlib.pyplot as plt
import streamlit as st

from prop_simulator import (
    STYLE_DESCRIPTIONS,
    SimulationConfig,
    build_simulation_report,
    calculate_expectancy,
    sample_paths,
)

st.set_page_config(page_title="Prop Firm Simulator", layout="wide")
st.title("Prop Firm Challenge Monte Carlo Simulator")
st.markdown(
    "### Test your edge with fixed risk, dynamic risk, and style-based recommendations"
)

st.sidebar.header("Simulation Parameters")

profit_target = st.sidebar.number_input("Profit Target ($)", value=3000, step=100)
dd_limit = st.sidebar.number_input("Trailing Drawdown Limit ($)", value=2000, step=100)
win_rate = st.sidebar.slider("Win Rate (%)", 40, 90, 60) / 100.0
profit_factor = st.sidebar.slider("Reward : Risk Multiple", 1.0, 3.0, 1.6, 0.1)
strategy_mode = st.sidebar.radio("System Type", ["Mechanical", "Discretionary"], index=0)
trader_style = st.sidebar.radio(
    "Recommendation Style",
    ["Aggressive", "Balanced", "Conservative"],
    index=1,
    help=(
        "Aggressive prioritizes speed, Balanced is the middle ground, "
        "and Conservative prioritizes survival."
    ),
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
    help=(
        "0 disables the rule. Example: 20 means no single winning trade "
        "can contribute more than 20% of the profit target."
    ),
)
num_sims = st.sidebar.slider("Number of Simulations", 1000, 10000, 3000, step=500)

config = SimulationConfig(
    profit_target=float(profit_target),
    dd_limit=float(dd_limit),
    win_rate=win_rate,
    profit_factor=profit_factor,
    strategy_mode=strategy_mode,
    be_trade_percent=float(be_trade_percent),
    consistency_limit_percent=float(consistency_limit_percent),
    num_sims=int(num_sims),
    trader_style=trader_style,
)

st.sidebar.metric("System Expectancy", f"{calculate_expectancy(config):.2f}R per trade")

st.sidebar.markdown("---")
st.sidebar.subheader("Documentation")
show_readme = st.sidebar.checkbox("Show README")

if show_readme:
    st.markdown("# README / Help")
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as readme_file:
            st.markdown(readme_file.read())
    else:
        st.error("README.md file not found in the app folder.")
    st.stop()


def format_optional(value):
    return "N/A" if value is None else value


def add_stats_box(ax, risk_dollars, summary):
    text = "\n".join(
        [
            f"Risk: ${risk_dollars}",
            f"Pass: {summary.pass_rate}%",
            f"Breach: {summary.breach_rate}%",
            f"Timeout: {summary.timeout_rate}%",
            f"Avg Pass Steps: {format_optional(summary.avg_steps_to_pass)}",
            f"Avg Pass Trades: {format_optional(summary.avg_trades_to_pass)}",
        ]
    )
    ax.text(
        0.98,
        0.02,
        text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="black", alpha=0.9),
    )


def plot_plan(ax, title, subtitle, config_value, recommendation, preferred_outcome, seed):
    paths = sample_paths(
        config=config_value,
        risk_dollars=recommendation.risk_dollars,
        dynamic=recommendation.dynamic,
        count=3,
        preferred_outcome=preferred_outcome,
        start_seed=seed,
    )

    for index, path in enumerate(paths):
        color = plt.cm.tab10(index)
        label = f"{path.outcome.title()} Path {index + 1}"
        ax.plot(path.equities, color=color, linewidth=2, label=label)
        ax.plot(path.trailing_floors, color=color, linestyle="--", alpha=0.5)

    ax.axhline(y=config_value.profit_target, color="green", linewidth=2, label="Pass Target")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=28)
    ax.text(
        0.5,
        1.01,
        subtitle,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
    )
    ax.set_xlabel("Simulation Steps")
    ax.set_ylabel("Profit / Loss ($)")
    ax.grid(True, alpha=0.3)
    add_stats_box(ax, recommendation.risk_dollars, recommendation.summary)
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(loc="upper left")


if st.button("Run Simulation", type="primary", use_container_width=True):
    with st.spinner("Running simulations..."):
        report = build_simulation_report(config=config, fixed_risk_amount=int(fixed_risk_amount))

    st.info(
        f"Recommendation Style: {config.trader_style} — "
        f"{STYLE_DESCRIPTIONS[config.trader_style]}"
    )

    consistency_suffix = (
        f"Consistency Cap: ${config.consistency_cap_amount:.0f} ({int(config.consistency_limit_percent)}%)"
        if config.consistency_cap_amount is not None
        else "No Consistency Cap"
    )

    st.markdown("### Recommendation Matrix")
    st.dataframe(report.matrix_rows, use_container_width=True)

    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    axs = axs.flatten()

    plot_plan(
        axs[0],
        f"1. FIXED ${report.fixed.risk_dollars} Risk",
        f"Your Current Style\n{consistency_suffix}",
        config,
        report.fixed,
        preferred_outcome=None,
        seed=100,
    )
    plot_plan(
        axs[1],
        f"2. DYNAMIC ${report.dynamic.risk_dollars} Risk",
        f"Rule: Halve Risk in Drawdown\n{consistency_suffix}",
        config,
        report.dynamic,
        preferred_outcome=None,
        seed=200,
    )
    plot_plan(
        axs[2],
        f"3. {config.trader_style.upper()} RECOMMENDED: Dynamic ${report.selected.risk_dollars} Risk",
        f"{report.selected.rationale}\n{consistency_suffix}",
        config,
        report.selected,
        preferred_outcome="pass",
        seed=report.selected.risk_dollars * 10,
    )
    plot_plan(
        axs[3],
        f"4. FASTEST SAFE: Dynamic ${report.fastest_safe.risk_dollars} Risk",
        f"{report.fastest_safe.rationale}\n{consistency_suffix}",
        config,
        report.fastest_safe,
        preferred_outcome="pass",
        seed=report.fastest_safe.risk_dollars * 20,
    )

    plt.tight_layout()
    st.pyplot(fig)
    st.caption(
        "Chart x-axis uses simulation steps. No-trade periods count as steps but not as executed trades."
    )
    st.success("Simulation complete.")
else:
    st.info("Adjust the settings in the sidebar and click Run Simulation to start.")

st.caption("Built with Streamlit • Monte Carlo Prop Firm Simulator")
