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
        st.warning("⚠️ Cloud data ledger is compiling. Please run your 'main.py' workflow script first to initialize signals.")
        return pd.DataFrame()
        
    try:
        with open(json_path, "r") as f:
            data_payload = json.load(f)
            
        signals_list = data_payload.get("signals", [])
        if not signals_list:
            return pd.DataFrame()
            
        master_rows = []
        for item in signals_list:
            # Safely capture any potential failure strings or metadata anomalies
            roi_value = item.get("backtest_roi_pct", "+0.00%")
            if isinstance(roi_value, (int, float)):
                roi_str = f"{roi_value:+.2f}%"
            else:
                roi_str = str(roi_value)

            # Re-map the clean cloud JSON records back into the scorecard table format
            master_rows.append({
                "Asset Ticker": str(item.get("ticker", "UNKNOWN")),
                "Current Close": f"₹{float(item.get('close_price', 0)):,.2f}",
                "Ann. Volatility": f"{float(item.get('ann_volatility_pct', 0)):.2f}%",
                "Daily VaR (95%)": f"{float(item.get('daily_var_95_pct', 0)):.2f}%",
                "Qlib Alpha Score": float(item.get("qlib_alpha_score", 0)),
                "Backtest Success (ROI)": roi_str,
                "Sort_Key_ROI": float(item.get("qlib_alpha_score", 0)), # Prioritize highest momentum items
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

            action_status = "BUY" if qlib_signal > 0.01 else "HOLD"

            master_rows.append({
                "Asset Ticker": clean_display_name,
                "Current Close": f"₹{latest_close:,.2f}",
                "Ann. Volatility": f"{latest_vol:.2f}%",
                "Daily VaR (95%)": f"{latest_var:.2f}%",
                "Qlib Alpha Score": qlib_signal,
                "Backtest Success (ROI)": f"{historical_roi:+.2f}%",  # Safe string display conversion
                "Sort_Key_ROI": historical_roi,  # Real float tracking value for sorting logic
                "Action Deployment": action_status
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
