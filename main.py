import os
import glob
import json
import logging
import time

import yaml
import requests
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use('Agg')  # Enforces a headless backend for safe server execution environments
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from openbb import obb

os.makedirs("data/output", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/output/run.log", mode="a"),
    ],
)
logger = logging.getLogger("quant_bot")


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
            avg_volume: float,
            tp1: float = 0.0,
            tp2: float = 0.0
    ):
        """Transmits a traditional text configuration log payload via Telegram bot API."""
        if not self.enabled:
            return

        clean_name = str(ticker).replace(".NS", "").replace(".BO", "").strip()
        initial_capital = 100000.0
        final_capital = initial_capital * (1.0 + (roi / 100.0))

        # Build dynamic strings for the take-profit matrix panel if values are provided
        tp_matrix_panel = ""
        if tp1 > 0 and tp2 > 0:
            tp_matrix_panel = (
                f"ðŸŽ¯ <b>VOLATILITY TAKE-PROFIT MATRIX:</b>\n"
                f" â€¢ Take-Profit 1 (50% Scalp): <b>â‚¹{tp1:,.2f}</b>\n"
                f" â€¢ Take-Profit 2 (Runner Target): <b>â‚¹{tp2:,.2f}</b>\n\n"
            )

        # Telegram text notification template layout
        message_payload = (
            f"âš¡ <b>QUANT STRATEGY SYSTEM: Bismillah TRIGGER</b> âš¡\n"
            f"ðŸ¤– <b>Status:</b> Automated bot alert dispatched\n"
            f"âš ï¸ <i>Please check Shariah status</i>\n\n"
            f"ðŸ“Œ <b>Asset Target:</b> #{clean_name}\n"
            f"ðŸ’° <b>Current Close Price:</b> â‚¹{price:,.2f}\n"
            f"ðŸ“ˆ <b>Qlib Alpha Score:</b> {alpha:+.4f}\n"
            f"ðŸ“Š <b>Current 14-Day RSI:</b> {rsi:.2f}\n"
            f"ðŸ”Š <b>Volume Telemetry:</b> {volume:,.0f} (20D Avg: {avg_volume:,.0f})\n\n"
            f"{tp_matrix_panel}"
            f"âš™ï¸ <b>LEAN SIMULATION PORTFOLIO MATRIX:</b>\n"
            f" â€¢ Initial Account Capital: â‚¹{initial_capital:,.2f}\n"
            f" â€¢ Final Strategy Capital: <b>â‚¹{final_capital:,.2f}</b>\n"
            f" â€¢ Net Strategy Profit ROI: <b>{roi:+.2f}%</b>\n\n"
            f"ðŸ“Š <b>Risk & Volatility Telemetry:</b>\n"
            f" â€¢ Trailing Ann. Volatility: {vol:.2f}%\n"
            f" â€¢ Daily Value at Risk (95%): {var:.2f}%\n\n"
            f"âž¡ï¸ <b>Execution Order:</b> Only for study- no buy/sell."
        )

        api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

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
                logger.info(f" âœ“ Telegram text alert delivered successfully via bot for {clean_name}!")
            else:
                error_description = response_data.get("description", response.text)
                logger.error(f" âœ• Telegram API Error: Status {response.status_code} | Description: {error_description}")

        except requests.exceptions.Timeout:
            logger.error(f" âœ• Telegram request timed out while sending alert for {clean_name}.")
        except requests.exceptions.RequestException as net_error:
            logger.error(f" âœ• Telegram connection failed: {net_error}")
        except Exception as unexpected_error:
            logger.error(f" âœ• Unexpected Telegram alert error: {unexpected_error}")

    def generate_and_send_visual_card(
            self, ticker: str, price: float, vol: float, var: float,
            alpha: float, roi: float, rsi: float, tp1: float, tp2: float
    ):
        """Renders a restrained, institutional-style signal card (single dark palette,
        thin borders instead of blocky color panels, two accent colors only)."""
        if not self.enabled:
            return

        clean_name = str(ticker).replace(".NS", "").replace(".BO", "").strip()

        # --- Professional palette: one background, one panel tone, one border tone,
        # a muted gold brand accent, and teal/rose reserved only for +/- values. ---
        BG = '#0B0F19'
        PANEL = '#111827'
        BORDER = '#26304A'
        TEXT_PRIMARY = '#E8EAF0'
        TEXT_SECONDARY = '#8A93A6'
        GOLD = '#C9A24B'
        POSITIVE = '#3FB88F'
        NEGATIVE = '#D9707A'

        def panel(x, y, w, h):
            ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=PANEL, edgecolor=BORDER,
                                            linewidth=1.0, zorder=1))

        fig, ax = plt.subplots(figsize=(7, 11), facecolor=BG)
        ax.set_xlim(0, 7)
        ax.set_ylim(0, 11)
        plt.axis('off')

        # Header â€” brand line + thin rule, no filled block
        ax.text(0.4, 10.5, "QUANT STRATEGY SYSTEM", color=TEXT_SECONDARY, fontsize=13,
                fontweight='bold', zorder=2)
        ax.text(0.4, 10.05, "SIGNAL TRIGGERED", color=GOLD, fontsize=22, fontweight='bold', zorder=2)
        ax.plot([0.4, 6.6], [9.75, 9.75], color=BORDER, linewidth=1.0, zorder=2)

        # Panel A: Asset Summary
        panel(0.3, 5.8, 3.0, 3.7)
        ax.text(0.5, 9.1, f"{clean_name}", color=TEXT_PRIMARY, fontsize=19, fontweight='bold', zorder=2)
        ax.text(0.5, 8.5, "CLOSE PRICE", color=TEXT_SECONDARY, fontsize=9, zorder=2)
        ax.text(0.5, 7.95, f"â‚¹{price:,.2f}", color=TEXT_PRIMARY, fontsize=20, fontweight='bold', zorder=2)
        alpha_color = POSITIVE if alpha > 0 else NEGATIVE
        ax.text(0.5, 7.35, "ALPHA SCORE", color=TEXT_SECONDARY, fontsize=9, zorder=2)
        ax.text(0.5, 6.95, f"{alpha:+.4f}", color=alpha_color, fontsize=13, fontweight='bold', zorder=2)
        ax.text(0.5, 6.45, f"14D RSI: {rsi:.2f}", color=TEXT_PRIMARY, fontsize=10, zorder=2)
        ax.text(0.5, 6.05, f"Volume: {vol:.2f}M", color=TEXT_PRIMARY, fontsize=10, zorder=2)

        # Panel B: Take-Profit Matrix â€” thin dividers, not solid color tiles
        panel(3.7, 5.8, 3.0, 3.7)
        ax.text(3.9, 9.1, "TAKE-PROFIT MATRIX", color=TEXT_SECONDARY, fontsize=10, fontweight='bold', zorder=2)
        ax.plot([3.9, 6.5], [8.9, 8.9], color=BORDER, linewidth=0.8, zorder=2)
        ax.text(3.9, 8.45, "TP1 Â· 50% Scalp", color=TEXT_SECONDARY, fontsize=9, zorder=2)
        ax.text(3.9, 8.0, f"â‚¹{tp1:,.2f}", color=POSITIVE, fontsize=15, fontweight='bold', zorder=2)
        ax.plot([3.9, 6.5], [7.6, 7.6], color=BORDER, linewidth=0.8, zorder=2)
        ax.text(3.9, 7.15, "TP2 Â· Runner Target", color=TEXT_SECONDARY, fontsize=9, zorder=2)
        ax.text(3.9, 6.7, f"â‚¹{tp2:,.2f}", color=POSITIVE, fontsize=15, fontweight='bold', zorder=2)

        # Panel C: Backtest ROI â€” thin radial gauge instead of an overflowing filled circle
        panel(0.3, 1.6, 3.0, 3.9)
        ax.text(0.5, 5.1, "BACKTEST ROI", color=TEXT_SECONDARY, fontsize=10, fontweight='bold', zorder=2)
        roi_color = POSITIVE if roi >= 0 else NEGATIVE
        gauge_fraction = min(abs(roi) / 50.0, 1.0)  # ring fills fully at +/-50% ROI
        ax.add_patch(patches.Wedge((1.8, 3.55), 0.8, 0, 360, width=0.18, facecolor=BORDER, zorder=2))
        if gauge_fraction > 0:
            ax.add_patch(patches.Wedge((1.8, 3.55), 0.8, 90 - 360 * gauge_fraction, 90,
                                        width=0.18, facecolor=roi_color, zorder=3))
        ax.text(1.8, 3.55, f"{roi:+.1f}%", color=TEXT_PRIMARY, fontsize=13, fontweight='bold',
                ha='center', va='center', zorder=4)
        ax.text(0.5, 2.2, "Net Strategy Return", color=TEXT_SECONDARY, fontsize=9, zorder=2)

        # Panel D: Risk & Volatility
        panel(3.7, 1.6, 3.0, 3.9)
        ax.text(3.9, 5.1, "RISK & VOLATILITY", color=TEXT_SECONDARY, fontsize=10, fontweight='bold', zorder=2)
        ax.text(3.9, 4.3, "Daily VaR (95%)", color=TEXT_SECONDARY, fontsize=9, zorder=2)
        ax.text(3.9, 3.85, f"{var:.2f}%", color=NEGATIVE, fontsize=16, fontweight='bold', zorder=2)
        ax.text(3.9, 2.7, "Study signal only â€” not investment advice.", color=TEXT_SECONDARY,
                fontsize=8.5, zorder=2, wrap=True)

        # Footer
        ax.plot([0.4, 6.6], [1.3, 1.3], color=BORDER, linewidth=1.0, zorder=2)
        ax.text(0.4, 0.85, "Execution Order: For research/study purposes â€” not a buy/sell recommendation.",
                color=TEXT_SECONDARY, fontsize=9, zorder=2)

        temp_img_path = f"data/output/{clean_name}_signal_card.png"
        os.makedirs(os.path.dirname(temp_img_path), exist_ok=True)
        plt.savefig(temp_img_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=200, bbox_inches='tight')
        plt.close(fig)

        send_photo_url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        try:
            with open(temp_img_path, 'rb') as photo_file:
                files = {'photo': photo_file}
                data = {
                    'chat_id': self.chat_id,
                    'caption': f"âš¡ <b>QUANT STRATEGY SYSTEM BUY ALERT: #{clean_name}</b> âš¡\n<i>Live visual analytical card generated by strategy bot.</i>",
                    'parse_mode': 'HTML'
                }
                response = requests.post(send_photo_url, files=files, data=data, timeout=10)

            try:
                response_data = response.json()
            except ValueError:
                response_data = {}

            if response.status_code == 200 and response_data.get("ok") is True:
                logger.info(f" âœ“ Telegram visual card delivered successfully to phone for {clean_name}!")
            else:
                error_description = response_data.get("description", response.text)
                logger.error(f" âœ• Telegram photo API Error: Status {response.status_code} | Description: {error_description}")
        except requests.exceptions.Timeout:
            logger.error(f" âœ• Telegram photo request timed out while sending alert for {clean_name}.")
        except requests.exceptions.RequestException as net_error:
            logger.error(f" âœ• Telegram connection failed for photo: {net_error}")
        except Exception as unexpected_error:
            logger.error(f" âœ• Unexpected Telegram photo alert error: {unexpected_error}")
# =====================================================================
# QUANT & MACHINE LEARNING FEATURE COMPUTE ENGINES
# =====================================================================

class QlibPredictiveEngine:
    def __init__(self):
        os.makedirs("data/alpha_features", exist_ok=True)

    def generate_qlib_alpha_features(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(col).lower() for col in df.columns]

        # FIX: Present Close divided by 5-day Historical Close
        df['qlib_momentum_5d'] = (df['close'] / df['close'].shift(5)) - 1

        # Mean reversion (Price distance from 20-day SMA)
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
        if df.empty:
            return 0.0
        latest_row = df.iloc[-1]
        return float((latest_row['qlib_momentum_5d'] * 0.4) + (latest_row['qlib_mean_reversion_20d'] * 0.6))


class LeanPortfolioStrategyEngine:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.slippage_pct = 0.0005
        self.stt_pct = 0.001

    def run_backtest_from_dataframe(self, df: pd.DataFrame) -> dict:
        if df is None or df.empty or len(df) < 20:
            return {
                "initial_capital": self.initial_capital,
                "final_value": self.initial_capital,
                "net_return_pct": "Failed Analysis",
                "max_drawdown_pct": 0.0,
                "sharpe_ratio": 0.0,
                "total_trades": 0
            }

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

        # Set end_date to None by default so it always fetches the latest live session
        self.end_date = self.config.get("end_date", None)
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
                f"{clean_ticker}.BO" if exchange_type == "BSE" or "BOM" in clean_ticker else f"{clean_ticker}.NS"
            )
        return wrapped_list

    def run_ingestion(self, ticker: str) -> pd.DataFrame:
        raw_path = f"data/raw/{ticker}_raw.csv"
        fetch_start = self.start_date
        existing_df = None

        # 1. Check if the ticker has historical data saved on disk
        if os.path.exists(raw_path):
            try:
                existing_df = pd.read_csv(raw_path, index_col=0, parse_dates=True)
                if not existing_df.empty:
                    last_recorded_date = existing_df.index.max()
                    next_day = (last_recorded_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
                    today_str = pd.Timestamp.now().strftime("%Y-%m-%d")

                    # If the cached file is already up-to-date, bypass the network request
                    if next_day > today_str:
                        return existing_df

                    # Incremental fetch: pull only missing candles starting after the last recorded date
                    fetch_start = next_day
            except Exception as cache_read_error:
                logger.warning(f"[{ticker}] Could not read cached raw file ({raw_path}): "
                                f"{type(cache_read_error).__name__}: {cache_read_error}. Refetching from scratch.")
                existing_df = None

        # 2. Fetch the required dataset (5 years if new, only delta days if existing)
        try:
            params = {
                "symbol": ticker,
                "provider": "yfinance",
                "start_date": fetch_start,
                "extra_params": {"adjustment": "unadjusted"}
            }
            if self.end_date:
                params["end_date"] = self.end_date

            res = obb.equity.price.historical(**params)
            new_df = res.to_df()

            if new_df.empty:
                # This is the "silent staleness" case: no exception was raised, the provider
                # just handed back zero rows for the requested window. Logged as a warning
                # (not an error) since it can legitimately happen on a day with no new session,
                # but if this fires for every ticker on a day that should have traded, that's
                # the signal something's wrong upstream (rate limit, bad date window, etc.).
                last_cached = existing_df.index.max().date() if (existing_df is not None and not existing_df.empty) else "none"
                logger.warning(f"[{ticker}] Provider returned 0 new rows for window "
                                f"start_date={fetch_start!r} (cached through {last_cached}). "
                                f"Falling back to cached/fail-safe data â€” price will NOT advance this run.")
                return existing_df if (
                            existing_df is not None and not existing_df.empty) else self._generate_fail_safe_data(
                    ticker)

            new_df.index = pd.to_datetime(new_df.index)

            # 3. Merge new records into the historical dataset
            if existing_df is not None and not existing_df.empty:
                combined_df = pd.concat([existing_df, new_df])
                combined_df = combined_df[~combined_df.index.duplicated(keep="last")].sort_index()
            else:
                combined_df = new_df.sort_index()

            # 4. Save updated data locally to disk
      
