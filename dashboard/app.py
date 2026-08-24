import os
import json
import pandas as pd
import streamlit as st

# =====================================================================
# SYSTEM DESIGN CONFIGURATIONS & MASTER THEME SETUP
# =====================================================================
st.set_page_config(
    page_title="Neuberg Quant Signal Ledger",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("⚡ Neuberg Institutional Signal Ledger Engine")
st.caption("Automated Multi-Asset Performance Ranking & Alpha Deployment Core")
st.markdown("---")

# =====================================================================
# DATA COMPILATION & CONTEXT INGESTION PIPELINE
# =====================================================================
@st.cache_data(ttl=60)
def compile_master_signal_ledger():
    """
    Reads the daily cloud-compiled output dataset directly from storage,
    formatting it into an institutional ranked dashboard ledger matrix.
    """
    json_path = "data/output/latest_market_signals.json"
    
    # Fallback guard to prevent UI crash if the JSON hasn't been built by a cloud run yet
    if not os.path.exists(json_path):
        return pd.DataFrame()
        
    try:
        with open(json_path, "r") as f:
            data_payload = json.load(f)
            
        signals_list = data_payload.get("signals", [])
        if not signals_list:
            return pd.DataFrame()
            
        master_rows = []
        # Locate this loop block inside dashboard/app.py around line 43
        for item in signals_list:
            # FIX 2: Safely read the real numerical parameter out of your cloud JSON file
            roi_value = item.get("backtest_roi_pct", 0.0)
            if isinstance(roi_value, (int, float)):
                roi_str = f"{roi_value:+.2f}%"
            else:
                roi_str = str(roi_value)

            master_rows.append({
                "Asset Ticker": str(item.get("ticker", "UNKNOWN")),
                "Current Close": f"₹{float(item.get('close_price', 0)):,.2f}",
                "Ann. Volatility": f"{float(item.get('ann_volatility_pct', 0)):.2f}%",
                "Daily VaR (95%)": f"{float(item.get('daily_var_95_pct', 0)):.2f}%",
                "Qlib Alpha Score": float(item.get("qlib_alpha_score", 0)),
                "Backtest Success (ROI)": roi_str, # Maps your real ROI values straight onto the screen table rows
                "Sort_Key_ROI": float(item.get("qlib_alpha_score", 0)), 
                "Action Deployment": str(item.get("action_status", "HOLD"))
            })

            
        master_df = pd.DataFrame(master_rows)
        
        # Sort completely by highest current momentum alpha signals
        master_df = master_df.sort_values(by="Sort_Key_ROI", ascending=False).reset_index(drop=True)
        master_df = master_df.drop(columns=["Sort_Key_ROI"])
        return master_df
        
    except Exception as err:
        st.error(f"✕ Critical error parsing automated data array layer: {err}")
        return pd.DataFrame()

# =====================================================================
# INTERACTIVE DATA PRESENTATION ENGINE LAYER
# =====================================================================
ledger_matrix = compile_master_signal_ledger()

if ledger_matrix.empty:
    st.warning("⚠️ High-order analytical databases are empty or compiling. Please run your background execution loop script ('python main.py') to synchronize files.")
else:
    st.subheader("📋 Top 10 High-Performing Asset Ledger")
    st.caption("Equities sorted directly by optimal backtest success metrics. Invalid rows are dynamically filtered out.")
    st.markdown("---")
    
    # Isolate your high-performing Top 10 target list matrix slice
    top_10_ledger = ledger_matrix.head(10)
    
    # 1. Macro Dashboard Summaries Summary Containers
    if not top_10_ledger.empty:
        lead_row = top_10_ledger.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Top Asset Current Close", value=str(lead_row["Current Close"]))
        with col2:
            st.metric(label="Top Asset Alpha Momentum Score", value=f"{lead_row['Qlib Alpha Score']:+.4f}")
        with col3:
            st.metric(label="Daily VaR (95%)", value=str(lead_row["Daily VaR (95%)"]))
        with col4:
            st.metric(label="Current Deployment Status", value=str(lead_row["Action Deployment"]))
            
    st.markdown("---")

    # 2. Dynamic Structural Row-Color Formatting Styles
    def apply_row_color_matrix(row):
        """Applies a soft dark green highlight row if the action status is BUY."""
        if row["Action Deployment"] == "BUY":
            return ["background-color: #1e3d2f; color: #73e6a4; font-weight: bold;"] * len(row)
        return [""] * len(row)

    # Compile the styled table wrapper frame
    styled_ledger = top_10_ledger.style.apply(apply_row_color_matrix, axis=1)
    
    # Project the formatted dataframe directly onto your web layout screen
    st.write(styled_ledger)
    
    # 3. Macro Metrics Footer Overview
    st.markdown("---")
    buy_count = len(top_10_ledger[top_10_ledger["Action Deployment"] == "BUY"])
    st.metric(label="Total Active BUY Alerts inside Top 10 Leaders", value=f"{buy_count} Tickers Triggered")
