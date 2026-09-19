import os
import json
import urllib.request  # 🟢 Added to fix the unresolved reference
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
    Safely decodes and extracts the nested quantitative matrix directly from the
    raw GitHub server network endpoints using native URL stream decoders.
    """
    # 🟢 DIRECT CONFIGURATION TO MATCH YOUR EXACT REPOSITORY TREE PROFILE
    repo_username = "mechvec-debug"
    repo_name = "AI_driven_Algorithmic_trading"
    branch_name = "main"

    raw_github_url = f"https://githubusercontent.com{repo_username}/{repo_name}/{branch_name}/data/output/latest_market_signals.json"
    master_rows = []

    try:
        # Request and download the file content smoothly over the web network link layer
        req = urllib.request.Request(
            raw_github_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )

        with urllib.request.urlopen(req) as url:
            raw_data_stream = url.read().decode('utf-8')
            database_payload = json.loads(raw_data_stream)

        # Extract the deep nested signals array component natively without pandas overhead crashes
        signals_list = database_payload.get("signals", [])

        for signal in signals_list:
            roi_val = signal.get("backtest_roi_pct", 0.0)
            if roi_val is None or isinstance(roi_val, str):
                roi_val = -999.0

            action_status = signal.get("action_status", "HOLD")
            peak_tracked = signal.get("highest_tracked_peak", 0.0)
            trailing_floor = signal.get("active_trailing_stop_floor", 0.0)
            target_tp1 = signal.get("take_profit_target_1", 0.0)
            target_tp2 = signal.get("take_profit_target_2", 0.0)

            clean_display_name = signal.get("ticker", "N/A")

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
                "Target Position Shares": signal.get("recommended_shares_to_buy", 0) if action_status == "BUY" else 0,
                "Capital Allocation (₹)": f"₹{signal.get('required_allocation_in_rupees', 0.0):,.2f}" if action_status == "BUY" else "₹0.00",
                "Peak Price (₹)": f"₹{peak_tracked:,.2f}" if action_status == "BUY" and peak_tracked > 0 else "N/A",
                "Trailing Stop Floor (₹)": f"₹{trailing_floor:,.2f}" if action_status == "BUY" and trailing_floor > 0 else "N/A",
                "Take Profit 1 (₹)": f"₹{target_tp1:,.2f}" if action_status == "BUY" and target_tp1 > 0 else "N/A",
                "Take Profit 2 (₹)": f"₹{target_tp2:,.2f}" if action_status == "BUY" and target_tp2 > 0 else "N/A"
            })
    except Exception as e:
        # Fallback to local parsing logic if network streams ever timed out
        local_path = "data/output/latest_market_signals.json"
        if os.path.exists(local_path):
            try:
                with open(local_path, "r") as f:
                    database_payload = json.load(f)
                signals_list = database_payload.get("signals", [])
                for signal in signals_list:
                    roi_val = signal.get("backtest_roi_pct", 0.0)
                    action_status = signal.get("action_status", "HOLD")
                    master_rows.append({
                        "Asset Ticker": signal.get("ticker", "N/A"),
                        "Industry Sector": signal.get("sector", "Other Diversified"),
                        "Current Close": f"₹{signal.get('close_price', 0.0):,.2f}",
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
            except Exception:
                pass

    if not master_rows:
        return pd.DataFrame()

    master_df = pd.DataFrame(master_rows)
    master_df = master_df.sort_values(by="Sort_Key_ROI", ascending=False).reset_index(drop=True)
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

    # =====================================================================
    # 🟢 FIXED ACCUMULATION PORTFOLIO SUMMARY CONTAINER (RAW STREAMING)
    # =====================================================================
    st.markdown("---")
    st.subheader("⚡ Live Account Performance Tracker & Portfolio Summary")
    st.caption(
        "Tracks simulated active execution sizing parameters, liquid asset ledger holdings, and account equity growth updates.")

    # Configure your exact repository directory endpoints
    repo_username = "mechvec-debug"
    repo_name = "AI_driven_Algorithmic_trading"
    branch_name = "main"

    # 🌐 STREAM DIRECTLY FROM GITHUB TO PREVENT CONTAINER COLD-BOOT BLOCKS
    raw_portfolio_url = f"https://githubusercontent.com{repo_username}/{repo_name}/{branch_name}/data/output/live_portfolio_ledger.json"

    portfolio_loaded = False
    portfolio_data = {}

    try:
        # Request and download the live ledger file over the internet link layer
        req_p = urllib.request.Request(
            raw_portfolio_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req_p) as url_p:
            raw_p_stream = url_p.read().decode('utf-8')
            portfolio_data = json.loads(raw_p_stream)
        portfolio_loaded = True
    except Exception:
        # Fallback to local file path parsing if network streams hit a connection block
        local_p_path = "data/output/live_portfolio_ledger.json"
        if os.path.exists(local_p_path):
            try:
                with open(local_p_path, "r") as p_f:
                    portfolio_data = json.load(p_f)
                portfolio_loaded = True
            except Exception:
                pass

    if not portfolio_loaded or not portfolio_data:
        st.info(
            "ℹ️ Account simulation ledger is currently empty. Run the broker agent component script ('python broker_agent.py') on your laptop or wait for the cloud workflow to complete to bring live ledger updates online.")
    else:
        p_telemetry = portfolio_data.get("account_telemetry", {})
        p_positions = portfolio_data.get("active_positions", {})

        # 1. Macro Summary Balance Scorecards
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric(
                label="Total Portfolio Value (Cash + Stock)",
                value=f"₹{p_telemetry.get('total_portfolio_value', 100000.0):,.2f}",
                delta=f"{p_telemetry.get('total_closed_roi_pct', 0.0):+.2f}% ROI"
            )
        with m_col2:
            st.metric(label="Available Cash Balance", value=f"₹{p_telemetry.get('available_cash', 100000.0):,.2f}")
        with m_col3:
            st.metric(label="Active Open Positions Count", value=f"{len(p_positions)} Assets Live")

        # 2. Active Holdings Grid Data Table
        if p_positions:
            st.markdown("##### 📋 Current Position Holding Matrix Ledger Details")
            positions_rows = []
            for t_code, p_details in p_positions.items():
                positions_rows.append({
                    "Asset Ticker": t_code,
                    "Industry Sector": p_details.get("sector", "Other Diversified"),
                    "Shares Held (Qty)": p_details.get("qty", 0),
                    "Average Cost Price": f"₹{p_details.get('entry_avg', 0.0):,.2f}",
                    "Take Profit 1": f"₹{p_details.get('tp1', 0.0):,.2f}",
                    "Take Profit 2": f"₹{p_details.get('tp2', 0.0):,.2f}",
                    "Active Trailing Stop Floor": f"₹{p_details.get('trailing_floor', 0.0):,.2f}",
                    "Peak Price Reached": f"₹{p_details.get('peak_close', 0.0):,.2f}"
                })
            st.dataframe(pd.DataFrame(positions_rows))
        else:
            st.info("💼 No active positions are currently held in the portfolio simulation ledger.")
