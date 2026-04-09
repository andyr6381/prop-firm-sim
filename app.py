import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os
import webbrowser

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
        
        fixed_stats = run_simulation(fixed_risk_amount, dynamic=False, num_sims=num_sims)
        dynamic_stats = run_simulation(fixed_risk_amount, dynamic=True, num_sims=num_sims)
        
        # Recommendation logic (simplified)
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

            score = (
                stats['pass_rate'] * 2
                - stats['blow_rate'] * 3
                - stats['avg_trades'] * 0.5
            )

            if score > best_score:
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

        st.success("Simulation Complete!")

else:
    st.info("👈 Adjust the settings in the sidebar and click **Run Simulation** to start.")

st.caption("Built with Streamlit • Monte Carlo Prop Firm Simulator")