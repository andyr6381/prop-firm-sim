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
win_rate = st.sidebar.slider("Win Rate (%)", 40, 90, 70) / 100.0
profit_factor = st.sidebar.slider("Profit Factor", 1.0, 3.0, 1.9, 0.1)
fixed_risk_amount = st.sidebar.number_input("Fixed Risk Amount ($)", value=400, step=25)
num_sims = st.sidebar.slider("Number of Simulations", 1000, 10000, 3000, step=500)

# Calculate expectancy
avg_loss_r = 1.0
avg_win_r = profit_factor
expected_r = (win_rate * avg_win_r) - ((1 - win_rate) * avg_loss_r)
st.sidebar.metric("System Expectancy", f"{expected_r:.2f}R per trade")

# ================== SIMULATION FUNCTIONS ==================
@st.cache_data
def simulate_one_path(risk_dollars, dynamic=False, seed=None, return_result=False):
    rng = np.random.default_rng(seed)
    equity = 0.0
    peak = 0.0
    equities = [equity]
    breach_floors = [-dd_limit]
    current_risk = risk_dollars
    
    for t in range(300):
        p_win = 0.45 if rng.random() < 0.15 else win_rate
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
            for _ in range(20):  # extend for visibility
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
            p_win = 0.45 if np.random.rand() < 0.15 else win_rate
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
        
        # Run recommendation
        best_score = -999
        recommended_risk = 250
        recommended_stats = None
        
        for risk in range(150, 551, 25):
            stats = run_simulation(risk, dynamic=True, num_sims=1500)
            score = stats['pass_rate'] * 2 - stats['blow_rate'] * 3 - stats['avg_trades'] * 0.5
            if score > best_score:
                best_score = score
                recommended_risk = risk
                recommended_stats = stats

        # ================== DISPLAY RESULTS ==================
        col1, col2, col3 = st.columns(3)
        
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
            st.subheader("Recommended")
            st.metric("Risk Size", f"${recommended_risk}")
            st.metric("Pass Rate", f"{recommended_stats['pass_rate']}%")
            st.metric("Blow Rate", f"{recommended_stats['blow_rate']}%")
            st.metric("Avg Trades", recommended_stats['avg_trades'])

        st.success("Simulation Complete!")

        # ================== CHARTS ==================
        st.subheader("Equity Curves Comparison")
        
        fig, axs = plt.subplots(1, 3, figsize=(18, 6))
        
        # Fixed Chart
        for i in range(3):
            path, floor = simulate_one_path(fixed_risk_amount, dynamic=False, seed=40+i)
            color = plt.cm.tab10(i)
            axs[0].plot(path, color=color, linewidth=2, alpha=0.9, label=f'Path {i+1}')
            axs[0].plot(floor, color=color, linestyle='--', alpha=0.5)
        axs[0].axhline(y=profit_target, color='green', linestyle='-', label='Target')
        axs[0].set_title(f"Fixed ${fixed_risk_amount} Risk")
        axs[0].legend()
        axs[0].grid(True, alpha=0.3)
        
        # Dynamic Chart
        for i in range(3):
            path, floor = simulate_one_path(fixed_risk_amount, dynamic=True, seed=100+i)
            color = plt.cm.tab10(i)
            axs[1].plot(path, color=color, linewidth=2, alpha=0.9, label=f'Path {i+1}')
            axs[1].plot(floor, color=color, linestyle='--', alpha=0.5)
        axs[1].axhline(y=profit_target, color='green', linestyle='-', label='Target')
        axs[1].set_title(f"Dynamic ${fixed_risk_amount} Risk")
        axs[1].legend()
        axs[1].grid(True, alpha=0.3)
        
        # Recommended Chart
        for i in range(3):
            path, floor = simulate_one_path(recommended_risk, dynamic=True, seed=200+i)
            color = plt.cm.tab10(i)
            axs[2].plot(path, color=color, linewidth=2, alpha=0.9, label=f'Path {i+1}')
            axs[2].plot(floor, color=color, linestyle='--', alpha=0.5)
        axs[2].axhline(y=profit_target, color='green', linestyle='-', label='Target')
        axs[2].set_title(f"Recommended: Dynamic ${recommended_risk}")
        axs[2].legend()
        axs[2].grid(True, alpha=0.3)
        
        st.pyplot(fig)

else:
    st.info("👈 Adjust the settings in the sidebar and click **Run Simulation** to start.")

st.caption("Built with Streamlit • Monte Carlo Prop Firm Simulator")