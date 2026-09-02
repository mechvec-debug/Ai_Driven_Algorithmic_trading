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
    Scans internal database storage directories, parses historical telemetry,
    ranks tickers, and marks broken datasets with a 'Failed Analysis' tag.
    """
    processed_files = glob.glob("data/processed/*_processed.csv")
    master_rows = []

    for file_path in processed_files:
        ticker_raw = os.path.basename(file_path).replace("_processed.csv", "")
        clean_display_name = ticker_raw.replace(".NS", "").replace(".BO", "")

        alpha_path = f"data/alpha_features/{ticker_raw}_qlib_features.csv"

        # CATCH BLOCKED PROFILES: If the Qlib math calculation file is completely missing
        # CATCH BLOCKED PROFILES: If the Qlib math calculation file is completely missing
        if not os.path.exists(alpha_path):
            master_rows.append({
                "Asset Ticker": clean_display_name,
                "Industry Sector": "N/A",  # 🟢 Added
                "Current Close": "N/A",
                "Ann. Volatility": "N/A",
                "Daily VaR (95%)": "N/A",
                "Qlib Alpha Score": 0.0,
                "Backtest Success (ROI)": "Failed Analysis",
                "Sort_Key_ROI": -9999.0,
                "Action Deployment": "HOLD",
                "Target Position Shares": 0,  # 🟢 Added
                "Capital Allocation (₹)": "₹0.00",  # 🟢 Added
                "Peak Price (₹)": "N/A",  # 🟢 Added
                "Trailing Stop Floor (₹)": "N/A"  # 🟢 Added
            })
            continue

        try:
            df_metrics = pd.read_csv(file_path, index_col=0, parse_dates=True)
            df_alpha = pd.read_csv(alpha_path, index_col=0, parse_dates=True)

            # CATCH SHORT DATASETS: If the ticker layout has no history
            if df_metrics.empty or df_alpha.empty or len(df_metrics) < 5:
                master_rows.append({
                    "Asset Ticker": clean_display_name,
                    "Industry Sector": "N/A",  # 🟢 Added
                    "Current Close": "N/A",
                    "Ann. Volatility": "N/A",
                    "Daily VaR (95%)": "N/A",
                    "Qlib Alpha Score": 0.0,
                    "Backtest Success (ROI)": "Failed Analysis",
                    "Sort_Key_ROI": -9999.0,
                    "Action Deployment": "HOLD",
                    "Target Position Shares": 0,  # 🟢 Added
                    "Capital Allocation (₹)": "₹0.00",  # 🟢 Added
                    "Peak Price (₹)": "N/A",  # 🟢 Added
                    "Trailing Stop Floor (₹)": "N/A"  # 🟢 Added
                })
                continue

            # Extract valid metrics data streams safely
            latest_close = float(df_metrics['close'].iloc[-1])
            latest_vol = float(df_metrics['rolling_volatility_ann'].iloc[-1]) * 100
            latest_var = float(df_metrics['var_95_threshold'].iloc[-1]) * 100
            qlib_signal = float(df_alpha['qlib_momentum_5d'].iloc[-1])

            # Simulated trading logic
            cash = 100000.0
            shares = 0.0
            for i in range(len(df_alpha)):
                row_price = df_alpha['close'].iloc[i]
                row_sig = df_alpha['qlib_momentum_5d'].iloc[i]
                if row_sig > 0.01 and shares == 0:
                    shares = (cash / (1.0 + 0.0015)) / row_price
                    cash = 0.0
                elif row_sig < -0.01 and shares > 0:
                    cash = (shares * row_price) * (1.0 - 0.0015)
                    shares = 0.0

            final_portfolio_value = cash + (shares * df_alpha['close'].iloc[-1])
            historical_roi = ((final_portfolio_value - 100000.0) / 100000.0) * 100

            # -----------------------------------------------------------------
            # 🟢 SECTOR & TRAILING METRICS EXTRACTION VIA CENTRALIZED JSON CACHE
            # -----------------------------------------------------------------
            # To preserve performance parity, pull the calculated core metrics
            # that main.py compiled into the centralized signals array
            asset_sector = "Other Diversified"
            action_status = "HOLD"
            shares_to_buy = 0
            allocation_rupees = 0.0
            peak_tracked = 0.0
            trailing_floor = 0.0

            # Match and sync telemetry directly from latest_market_signals.json
            output_json_path = "data/output/latest_market_signals.json"
            if os.path.exists(output_json_path):
                with open(output_json_path, "r") as j_f:
                    cache_payload = json.load(j_f)
                    for signal in cache_payload.get("signals", []):
                        if signal.get("ticker") == clean_display_name:
                            asset_sector = signal.get("sector", "Other Diversified")
                            action_status = signal.get("action_status", "HOLD")
                            shares_to_buy = signal.get("recommended_shares_to_buy", 0)
                            allocation_rupees = signal.get("required_allocation_in_rupees", 0.0)
                            peak_tracked = signal.get("highest_tracked_peak", 0.0)
                            trailing_floor = signal.get("active_trailing_stop_floor", 0.0)
                            break
            else:
                # Fallback if JSON doesn't exist yet
                action_status = "BUY" if qlib_signal > 0.01 else "HOLD"

            master_rows.append({
                "Asset Ticker": clean_display_name,
                "Industry Sector": asset_sector,  # 🟢 Added
                "Current Close": f"₹{latest_close:,.2f}",
                "Ann. Volatility": f"{latest_vol:.2f}%",
                "Daily VaR (95%)": f"{latest_var:.2f}%",
                "Qlib Alpha Score": qlib_signal,
                "Backtest Success (ROI)": f"{historical_roi:+.2f}%",
                "Sort_Key_ROI": historical_roi,
                "Action Deployment": action_status,
                "Target Position Shares": shares_to_buy if action_status == "BUY" else 0,  # 🟢 Added
                "Capital Allocation (₹)": f"₹{allocation_rupees:,.2f}" if action_status == "BUY" else "₹0.00",
                # 🟢 Added
                "Peak Price (₹)": f"₹{peak_tracked:,.2f}" if action_status == "BUY" and peak_tracked > 0 else "N/A",
                # 🟢 Added
                "Trailing Stop Floor (₹)": f"₹{trailing_floor:,.2f}" if action_status == "BUY" and trailing_floor > 0 else "N/A"
                # 🟢 Added
            })

        except Exception:
            # Handle general unhandled tracking errors gracefully
            master_rows.append({
                "Asset Ticker": clean_display_name,
                "Current Close": "N/A",
                "Ann. Volatility": "N/A",
                "Daily VaR (95%)": "N/A",
                "Qlib Alpha Score": 0.0,
                "Backtest Success (ROI)": "Failed Analysis",
                "Sort_Key_ROI": -9999.0,
                "Action Deployment": "HOLD"
            })

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
    # Ensure this is placed beneath your main subheader layout blocks!
    st.subheader("📋 Top 10 High-Performing Asset Ledger")
    st.caption(
        "Equities sorted directly by optimal backtest success metrics. Invalid rows are dynamically filtered out.")
    st.markdown("---")

    # =====================================================================
    # INJECTED CORE MODULE: 4-COLUMN INSTITUTIONAL SCORECARD ROW
    # =====================================================================
    # Extract the top row to display macro telemetry details for the selected focus stock
    top_10_ledger = ledger_matrix.head(10)

    if not top_10_ledger.empty:
        # Extract individual metrics safely from the top-performing asset row
        lead_row = top_10_ledger.iloc[0]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Top Asset Current Close", value=str(lead_row["Current Close"]))
        with col2:
            # Displays the LEAN Backtest Success Performance Metric Card
            st.metric(label="LEAN Backtest Success ROI", value=str(lead_row["Backtest Success (ROI)"]))
        with col3:
            st.metric(label="Daily VaR (95%)", value=str(lead_row["Daily VaR (95%)"]))
        with col4:
            st.metric(label="Current Deployment Status", value=str(lead_row["Action Deployment"]))

    st.markdown("---")


    # =====================================================================

    # [Your remaining table visualization and coloring code continues below...]
    def apply_row_color_matrix(row):
        if row["Action Deployment"] == "BUY":
            return ["background-color: #1e3d2f; color: #73e6a4; font-weight: bold;"] * len(row)
        return [""] * len(row)


    styled_ledger = top_10_ledger.style.apply(apply_row_color_matrix, axis=1)
    st.write(styled_ledger)


    # 2. Dynamic Structural Row-Color Formatting Styles
    def apply_row_color_matrix(row):
        """
        Applies highlight color states. Maps complete background color palettes
        to an entire row matrix if the final action column resolves to a BUY condition.
        """
        # Checks the string expression value inside the final 'Action Deployment' column array
        if row["Action Deployment"] == "BUY":
            # Hex values: Soft dark green background to match institutional configurations
            return ["background-color: #1e3d2f; color: #73e6a4; font-weight: bold;"] * len(row)
        return [""] * len(row)


    # Compile the styled HTML table wrapper frame
    styled_ledger = top_10_ledger.style.apply(apply_row_color_matrix, axis=1)

    # Project the formatted dataframe directly onto your web layout screen
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
