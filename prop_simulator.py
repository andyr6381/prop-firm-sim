num_sims = st.sidebar.slider("Number of Simulations", 1000, 10000, 3000, step=500)
st.sidebar.markdown("---")
st.sidebar.markdown("### Help / Documentation")
st.sidebar.markdown(
    "[Open Full README](https://github.com/andyr6381/prop-firm-sim/blob/main/README.md)"
)

with st.sidebar.expander("How This Simulator Works"):
    st.markdown(
        """
### Mechanical Mode
- Every trade is either a full winner or full loser.
- Winner size = Reward : Risk multiple
- Loser size = -1R

### Discretionary Mode
- A percentage of trades become breakeven scratches.
- Remaining trades still use the normal win/loss model.

### Dynamic Risk
- Uses full risk while at a new equity high.
- Halves risk whenever equity is below the previous peak.

### Streak Modeling
- Hot streaks temporarily improve win rate.
- Cold streaks temporarily reduce win rate.
- Quiet periods occasionally skip trades.

### Recommendations
- Safest = highest pass rate with lowest risk.
- Fastest Safe = quickest realistic way to pass.
        """
    )