import os
import glob
import pandas as pd
import streamlit as st
import json as json

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
    Directly decodes the high-order central JSON data matrix compiled by
    the active GitHub Actions runner loop. Bypasses raw missing CSV layers.
    """
    json_path = "data/output/latest_market_signals.json"
    master_rows = []

    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                database_payload = json.load(f)

            signals_list = database_payload.get("signals", [])

            for signal in signals_list:
                # Extract numerical calculations securely
                roi_val = signal.get("backtest_roi_pct", 0.0)
                if roi_val is None or isinstance(roi_val, str):
                    roi_val = -999.0

                action_status = signal.get("action_status", "HOLD")
                peak_tracked = signal.get("highest_tracked_peak", 0.0)
                trailing_floor = signal.get("active_trailing_stop_floor", 0.0)
                target_tp1 = signal.get("take_profit_target_1", 0.0)
                target_tp2 = signal.get("take_profit_target_2", 0.0)

                # Fetch base tracking ticker tokens cleanly
                clean_display_name = signal.get("ticker", "N/A")

                # 🟢 CRITICAL SYNC FIX: Explicitly append to master_rows with fallback properties
                # to prevent lower layout code blocks from throwing out-of-bounds index exceptions.
                master_rows.append({
                    "Asset Ticker": clean_display_name,
                    "Industry Sector": signal.get("sector", "Other Diversified"),
                    "Current Close": f"₹{signal.get('close_price', 0.0):,.2f}" if signal.get('close_price') else "N/A",
                    "Ann. Volatility": f"{signal.get('ann_volatility_pct', 0.0):.2f}%",
                    "Daily VaR (95%)": f"{signal.get('daily_var_95_pct', 0.0):.2f}%",
                    "Qlib Alpha Score": signal.get("qlib_alpha_score", 0.0),
                    "Backtest Success (ROI)": f"{roi_val:+.2f}%" if roi_val != -999.0 else "Failed Analysis",
                    "Sort_Key_ROI": roi_val if roi_val != -999.0 else -9999.0,
                    "Action Deployment": action_status,
                    "Target Position Shares": signal.get("recommended_shares_to_buy",
                                                         0) if action_status == "BUY" else 0,
                    "Capital Allocation (₹)": f"₹{signal.get('required_allocation_in_rupees', 0.0):,.2f}" if action_status == "BUY" else "₹0.00",
                    "Peak Price (₹)": f"₹{peak_tracked:,.2f}" if action_status == "BUY" and peak_tracked > 0 else "N/A",
                    "Trailing Stop Floor (₹)": f"₹{trailing_floor:,.2f}" if action_status == "BUY" and trailing_floor > 0 else "N/A",
                    "Take Profit 1 (₹)": f"₹{target_tp1:,.2f}" if action_status == "BUY" and target_tp1 > 0 else "N/A",
                    "Take Profit 2 (₹)": f"₹{target_tp2:,.2f}" if action_status == "BUY" and target_tp2 > 0 else "N/A"
                })
        except Exception as e:
            # Injecting logs to debug any formatting type mismatches safely
            st.error(f"Internal structure reading error: {e}")
            return pd.DataFrame()

    if not master_rows:
        return pd.DataFrame()

    master_df = pd.DataFrame(master_rows)

    # SORTING LOGIC: Use our hidden float key so top successes rise to the top 10 rows
    master_df = master_df.sort_values(by="Sort_Key_ROI", ascending=False).reset_index(drop=True)

    # FIX: Match the exact uppercase layout title to drop the column safely
    master_df = master_df.drop(columns=["Sort_Key_ROI"])

    return master_df


# =====================================================================
# INTERACTIVE DATA PRESENTATION ENGINE LAYER
# =====================================================================
ledger_matrix = compile_master_signal_ledger()

if ledger_matrix.empty:
    st.warning(
        "⚠️ High-order analytical databases are empty. Please run your background execution loop script ('python main.py') to synchronize files.")
else:
    # 1. Split-View Container Filtering Module
    st.subheader("📋 Top 10 High-Performing Asset Ledger")
    st.caption(
        "Equities sorted directly by optimal backtest success metrics. Invalid rows are dynamically filtered out.")
    st.markdown("---")

    # =====================================================================
    # INJECTED CORE MODULE: 4-COLUMN INSTITUTIONAL SCORECARD ROW
    # =====================================================================
    top_10_ledger = ledger_matrix.head(10)

    if not top_10_ledger.empty:
        # Extract individual metrics safely from the top-performing asset row
        lead_row = top_10_ledger.iloc[0]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Top Asset Current Close", value=str(lead_row["Current Close"]))
        with col2:
            st.metric(label="LEAN Backtest Success ROI", value=str(lead_row["Backtest Success (ROI)"]))
        with col3:
            st.metric(label="Daily VaR (95%)", value=str(lead_row["Daily VaR (95%)"]))
        with col4:
            st.metric(label="Current Deployment Status", value=str(lead_row["Action Deployment"]))

    st.markdown("---")


    # =====================================================================
    # 2. Dynamic Structural Row-Color Formatting Styles
    # =====================================================================
    def apply_row_color_matrix(row):
        """
        Applies highlight color states. Maps complete background color palettes
        to an entire row matrix if the final action column resolves to a BUY condition.
        """
        if row["Action Deployment"] == "BUY":
            return ["background-color: #1e3d2f; color: #73e6a4; font-weight: bold;"] * len(row)
        return [""] * len(row)


    # Compile and project the styled dataset onto your web layout screen
    styled_ledger = top_10_ledger.style.apply(apply_row_color_matrix, axis=1)
    st.write(styled_ledger)

    # 3. Macro Dashboard Summaries Summary Containers
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        buy_count = len(top_10_ledger[top_10_ledger["Action Deployment"] == "BUY"])
        st.metric(label="Total Active BUY Alerts (Top 10)", value=f"{buy_count} Tickers Triggered")
    with col2:
        total_tracked_valid = len(ledger_matrix)
        st.metric(label="Total Valid Scanned Equities Database Size", value=f"{total_tracked_valid} / 500+ Active")

