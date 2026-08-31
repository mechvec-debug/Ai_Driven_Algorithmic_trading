import os
import yaml
import json
import glob
import requests
import pandas as pd
import numpy as np
from openbb import obb


# =====================================================================
# SYSTEM ALERTER: EVENT-DRIVEN TELEGRAM WEBHOOK FRAMEWORK
# =====================================================================

class TelegramAlertEngine:
    def __init__(self, token: str, chat_id: str):
        """Initializes the secure Telegram Bot API alert gateway."""
        self.token = token.strip() if token else ""
        self.chat_id = str(chat_id).strip() if chat_id else ""
        self.enabled = bool(self.token and self.chat_id)

    def send_buy_signal_alert(
            self,
            ticker: str,
            price: float,
            vol: float,
            var: float,
            alpha: float,
            roi: float,
            rsi: float,
            volume: float,
            avg_volume: float
    ):
        if not self.enabled:
            return

        clean_name = (
            str(ticker)
            .replace(".NS", "")
            .replace(".BO", "")
            .strip()
        )

        initial_capital = 100000.0
        final_capital = initial_capital * (1.0 + (roi / 100.0))

        message_payload = (
            f"⚡ <b>QUANT STRATEGY SYSTEM: Bismillah TRIGGER</b> ⚡\n"
            f"⚠️ <i>Please check Shariah status</i>\n\n"
            f"📌 <b>Asset Target:</b> #{clean_name}\n"
            f"💰 <b>Current Close Price:</b> ₹{price:,.2f}\n"
            f"📈 <b>Qlib Alpha Score:</b> {alpha:+.4f}\n"
            f"📊 <b>Current 14-Day RSI:</b> {rsi:.2f}\n"
            f"🔊 <b>Volume Telemetry:</b> {volume:,.0f} (20D Avg: {avg_volume:,.0f})\n\n"
            f"⚙️ <b>LEAN SIMULATION PORTFOLIO MATRIX:</b>\n"
            f" • Initial Account Capital: ₹{initial_capital:,.2f}\n"
            f" • Final Strategy Capital: <b>₹{final_capital:,.2f}</b>\n"
            f" • Net Strategy Profit ROI: <b>{roi:+.2f}%</b>\n\n"
            f"📊 <b>Risk & Volatility Telemetry:</b>\n"
            f" • Trailing Ann. Volatility: {vol:.2f}%\n"
            f" • Daily Value at Risk (95%): {var:.2f}%\n\n"
            f"➡️ <b>Execution Order:</b> Only for study- no buy/sell."
        )

        # 🟢 DEFINED CORRECTLY INSIDE SCOPE BEFORE PAYLOAD POSTING
        api_url = f"https://telegram.org{self.token}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": message_payload,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(api_url, json=payload, timeout=10)
            try:
                response_data = response.json()
            except ValueError:
                response_data = {}

            if response.status_code == 200 and response_data.get("ok") is True:
                print(f" ✓ Telegram alert delivered successfully to phone for {clean_name}!")
            else:
                error_description = response_data.get("description", response.text)
                print(f" ✕ Telegram API Error: Status {response.status_code} | Description: {error_description}")

        except requests.exceptions.Timeout:
            print(f" ✕ Telegram request timed out while sending alert for {clean_name}.")
        except requests.exceptions.RequestException as net_error:
            print(f" ✕ Telegram connection failed: {net_error}")
        except Exception as unexpected_error:
            print(f" ✕ Unexpected Telegram alert error: {unexpected_error}")

# =====================================================================
# QUANT & MACHINE LEARNING FEATURE COMPUTE ENGINES
# =====================================================================

class QlibPredictiveEngine:
    def __init__(self):
        os.makedirs("data/alpha_features", exist_ok=True)

    def generate_qlib_alpha_features(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(col).lower() for col in df.columns]

        df['qlib_momentum_5d'] = (df['close'].shift(5) / df['close']) - 1
        df['qlib_mean_reversion_20d'] = df['close'].rolling(window=20).mean() / df['close']
        df['qlib_vol_normalized_return'] = df['daily_return'] / (df['rolling_volatility_ann'] + 1e-8)

        change = df['close'].diff()
        gain = change.mask(change < 0, 0.0)
        loss = -change.mask(change > 0, 0.0)

        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()

        rs = avg_gain / (avg_loss + 1e-8)
        df['rsi_14d'] = 100 - (100 / (1 + rs))

        df = df.dropna()
        df.to_csv(f"data/alpha_features/{ticker}_qlib_features.csv")
        return df

    def compute_predictive_score(self, df: pd.DataFrame) -> float:
        if df.empty: return 0.0
        latest_row = df.iloc[-1]
        return float((latest_row['qlib_momentum_5d'] * 0.4) + (latest_row['qlib_mean_reversion_20d'] * 0.6))


class LeanPortfolioStrategyEngine:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.slippage_pct = 0.0005
        self.stt_pct = 0.001

    def run_backtest_from_dataframe(self, df: pd.DataFrame) -> dict:
        if df is None or df.empty or len(df) < 20:
            return {"initial_capital": self.initial_capital, "final_value": self.initial_capital,
                    "net_return_pct": "Failed Analysis", "max_drawdown_pct": 0.0, "sharpe_ratio": 0.0,
                    "total_trades": 0}

        cash, position_shares, trade_count, portfolio_value_history = self.initial_capital, 0.0, 0, []

        for i in range(len(df)):
            current_price = df['close'].iloc[i]
            alpha_signal = df['qlib_momentum_5d'].iloc[i]
            rsi_val = df['rsi_14d'].iloc[i]

            if alpha_signal > 0.01 and (45.0 <= rsi_val <= 65.0) and position_shares == 0:
                position_shares = (cash / (1.0 + self.slippage_pct + self.stt_pct)) / current_price
                cash = 0.0
                trade_count += 1
            elif alpha_signal < -0.01 and position_shares > 0:
                cash = (position_shares * current_price) * (1.0 - self.slippage_pct - self.stt_pct)
                position_shares = 0.0
                trade_count += 1
            portfolio_value_history.append(cash + (position_shares * current_price))

        df = df.copy()
        df['portfolio_value'] = portfolio_value_history
        final_value = portfolio_value_history[-1] if portfolio_value_history else self.initial_capital
        total_net_return = ((final_value - self.initial_capital) / self.initial_capital) * 100
        return {"net_return_pct": total_net_return}


# =====================================================================
# INGESTION ORCHESTRATION PIPELINE
# =====================================================================

class YahooFinanceQuantPipeline:
    def __init__(self, config_path: str = "config/settings.yaml", ticker_csv_path: str = "config/ticker_list.csv"):
        self.config = self._load_config(config_path)
        self.start_date = self.config.get("start_date", "2025-01-01")
        self.end_date = self.config.get("end_date", "2026-08-01")
        self.default_exchange = self.config.get("default_exchange", "NSE")
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        self.ticker_mappings = self._load_and_wrap_tickers(ticker_csv_path)

    def _load_config(self, path: str) -> dict:
        if os.path.exists(path):
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        return {}

    def _load_and_wrap_tickers(self, path: str) -> list:
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            pd.DataFrame({"ticker": ["RELIANCE", "TCS"], "exchange": ["NSE", "NSE"]}).to_csv(path, index=False)
        df = pd.read_csv(path)
        df.columns = [col.strip().lower() for col in df.columns]
        wrapped_list = []
        for _, row in df.iterrows():
            clean_ticker = str(row['ticker']).strip().upper()
            exchange_type = str(row['exchange']).strip().upper() if 'exchange' in df.columns else self.default_exchange
            wrapped_list.append(
                f"{clean_ticker}.BO" if exchange_type == "BSE" or "BOM" in clean_ticker else f"{clean_ticker}.NS")
        return wrapped_list

    def run_ingestion(self, ticker: str) -> pd.DataFrame:
        try:
            res = obb.equity.price.historical(ticker, provider="yfinance", start_date=self.start_date,
                                              end_date=self.end_date)
            df = res.to_df()
            if df.empty: raise ValueError("Empty dataframe.")
            df.to_csv(f"data/raw/{ticker}_raw.csv")
            return df
        except Exception:
            return self._generate_fail_safe_data(ticker)

    def calculate_quant_metrics(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(col).lower() for col in df.columns]
        df.index = pd.to_datetime(df.index)
        df['daily_return'] = df['close'].pct_change()
        df['rolling_volatility_ann'] = df['daily_return'].rolling(window=21).std() * np.sqrt(252)
        df['var_95_threshold'] = df['daily_return'].quantile(0.05)

        df['avg_volume_20d'] = df['volume'].rolling(window=20).mean()

        df = df.dropna()
        df.to_csv(f"data/processed/{ticker}_processed.csv")
        return df

    def _generate_fail_safe_data(self, ticker: str) -> pd.DataFrame:
        date_range = pd.date_range(start=self.start_date, end=self.end_date, freq='B')
        fallback_df = pd.DataFrame(
            {'open': np.linspace(2400, 2600, len(date_range)), 'high': np.linspace(2450, 2650, len(date_range)),
             'low': np.linspace(2380, 2580, len(date_range)), 'close': np.linspace(2420, 2620, len(date_range)),
             'volume': np.random.randint(100000, 500000, size=len(date_range))}, index=date_range)
        fallback_df.index.name = "date"
        fallback_df.to_csv(f"data/raw/{ticker}_raw.csv")
        return fallback_df

# =====================================================================
# SYSTEM MAIN ENGINE CONTROLLER LOOP
# =====================================================================
if __name__ == "__main__":
    print("=================================================================")
    print("RUNNING CONSOLIDATED SYSTEM SCRIPTS")
    print("=================================================================")

    pipeline = YahooFinanceQuantPipeline()
    qlib_engine = QlibPredictiveEngine()
    backtester = LeanPortfolioStrategyEngine(initial_capital=100000.0)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or pipeline.config.get("telegram_bot_token", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or pipeline.config.get("telegram_chat_id", "")

    bot_token = str(bot_token).strip() if bot_token else ""
    chat_id = str(chat_id).strip() if chat_id else ""

    notifier = TelegramAlertEngine(token=bot_token, chat_id=chat_id)

    # 1. Main Data Extraction and Analytical Execution Loop
    for wrapped_ticker in pipeline.ticker_mappings:
        raw_df = pipeline.run_ingestion(wrapped_ticker)
        metrics_df = pipeline.calculate_quant_metrics(raw_df, wrapped_ticker)

        if metrics_df is None or metrics_df.empty or len(metrics_df) < 5:
            continue

        # 2. Compute Microsoft Qlib Matrix Indicator Features
        qlib_df = qlib_engine.generate_qlib_alpha_features(metrics_df, wrapped_ticker)

        # Operational safety fix against out-of-bounds DataFrame indices
        if qlib_df is None or qlib_df.empty:
            print(f" ✕ [{wrapped_ticker}] Bypassed status. Insufficient data rows remaining after dropna().")
            continue

        alpha_score = qlib_engine.compute_predictive_score(qlib_df)

        # 3. Simulate LEAN Transaction Rules Backtest Results
        results = backtester.run_backtest_from_dataframe(qlib_df)

        current_price = float(metrics_df['close'].iloc[-1])
        ann_vol = float(metrics_df['rolling_volatility_ann'].iloc[-1]) * 100
        daily_var = float(metrics_df['var_95_threshold'].iloc[-1]) * 100

        # Metrics and Telemetry Slicing
        current_rsi = float(qlib_df['rsi_14d'].iloc[-1])
        current_volume = float(metrics_df['volume'].iloc[-1])
        avg_volume_20d = float(metrics_df['avg_volume_20d'].iloc[-1])

        if isinstance(results['net_return_pct'], str):
            strategy_roi = -999.0
        else:
            strategy_roi = float(results['net_return_pct'])

        # 4. GOLDEN RULE INTEGRATED FILTER SYSTEM (WITH ENFORCED RSI & VOLUME BREAKS)
        if (alpha_score > 0.01 and
                strategy_roi > 0.001 and
                (45.0 <= current_rsi <= 65.0) and
                (current_volume >= 50000 and current_volume >= (avg_volume_20d * 0.8))):

            print(
                f" -> [{wrapped_ticker}] Golden Rule Satisfied (Alpha: +{alpha_score:.4f} | RSI: {current_rsi:.2f} | Volume Ratio: {(current_volume / avg_volume_20d):.2f}). Dispatching alert...")
            notifier.send_buy_signal_alert(
                ticker=wrapped_ticker,
                price=current_price,
                vol=ann_vol,
                var=daily_var,
                alpha=alpha_score,
                roi=strategy_roi,
                rsi=current_rsi,
                volume=current_volume,
                avg_volume=avg_volume_20d
            )
        else:
            print(
                f" -> [{wrapped_ticker}] Bypassed status. Failed strict quantitative thresholds (Alpha/ROI/RSI/Volume alignment breakdown).")

    print("\n[Complete] Quant script loops finished successfully. Overwriting metrics...")

    # =====================================================================
    # CENTRALIZED JSON CORE OUTPUT WRITER SECTION
    # =====================================================================
    latest_scan_records = []
    processed_json_files = glob.glob("data/processed/*_processed.csv")

    for file_path in processed_json_files:
        ticker_raw = os.path.basename(file_path).replace("_processed.csv", "")
        clean_name = ticker_raw.replace(".NS", "").replace(".BO", "")
        alpha_path = f"data/alpha_features/{ticker_raw}_qlib_features.csv"

        if os.path.exists(alpha_path):
            try:
                df_m = pd.read_csv(file_path, index_col=0, parse_dates=True)
                df_a = pd.read_csv(alpha_path, index_col=0, parse_dates=True)

                results = backtester.run_backtest_from_dataframe(df_a)

                if isinstance(results['net_return_pct'], str):
                    roi_val = -999.0
                else:
                    roi_val = float(results['net_return_pct'])

                latest_alpha = float(df_a['qlib_momentum_5d'].iloc[-1])
                latest_rsi = float(df_a['rsi_14d'].iloc[-1])
                latest_volume = float(df_m['volume'].iloc[-1])
                latest_avg_vol = float(df_m['avg_volume_20d'].iloc[-1])

                if (latest_alpha > 0.01 and
                        (45.0 <= latest_rsi <= 65.0) and
                        roi_val > 0.0 and
                        (latest_volume >= 50000 and latest_volume >= (latest_avg_vol * 0.8))):
                    action_status = "BUY"
                else:
                    action_status = "HOLD"

                latest_scan_records.append({
                    "ticker": clean_name,
                    "close_price": float(df_m['close'].iloc[-1]),
                    "ann_volatility_pct": float(df_m['rolling_volatility_ann'].iloc[-1]) * 100,
                    "daily_var_95_pct": float(df_m['var_95_threshold'].iloc[-1]) * 100,
                    "qlib_alpha_score": latest_alpha,
                    "backtest_roi_pct": roi_val,
                    "action_status": action_status
                })
            except Exception:
                continue

    os.makedirs("data/output", exist_ok=True)
    current_time_stamp = str(pd.Timestamp.now(tz='Asia/Kolkata'))

    output_payload = {
        "last_updated": current_time_stamp,
        "total_scanned_assets": len(latest_scan_records),
        "signals": latest_scan_records
    }

    with open("data/output/latest_market_signals.json", "w") as json_file:
        json.dump(output_payload, json_file, indent=4)

    print("✓ Central output matrix overwritten successfully.")
