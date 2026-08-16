import os
import pandas as pd
import numpy as np


class QlibPredictiveEngine:
    def __init__(self):
        """
        Initializes the Qlib Alpha Expression engine framework.
        Creates feature repository targets safely.
        """
        os.makedirs("data/alpha_features", exist_ok=True)

    def generate_qlib_alpha_features(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Applies mathematical formulas inspired by the Microsoft Qlib Alpha158
        and Quantitative Investment definitions to create predictive signals.
        """
        print(f"-> Transforming {ticker} data via Qlib Alpha Matrix Framework...")
        df = df.copy()

        # 1. Qlib Expression: Ref(Close, 5) / Close - 1 (5-Day Momentum Directional Score)
        # Predicts whether the stock is undergoing short-term exhaustion or trend acceleration
        df['qlib_momentum_5d'] = (df['close'].shift(5) / df['close']) - 1

        # 2. Qlib Expression: Mean(Close, 20) / Close (20-Day Mean Reversion Signal)
        # Captures deviation from the structural moving average of the stock price
        df['qlib_mean_reversion_20d'] = df['close'].rolling(window=20).mean() / df['close']

        # 3. Qlib Expression: Volatility Adjusted Velocity Factor
        # Normalizes daily price movement vectors against rolling volatility spikes
        df['qlib_vol_normalized_return'] = df['daily_return'] / (df['rolling_volatility_ann'] + 1e-8)

        # 4. Target Generation (Label): 5-Day Forward Return Matrix
        # This acts as the mathematical label that predictive models attempt to match
        df['target_forward_return_5d'] = df['close'].shift(-5) / df['close'] - 1

        # Drop boundary NaN rows resulting from rolling window shifts safely
        df = df.dropna()

        # Archive the matrix locally to feed machine learning workflows
        feature_path = f"data/alpha_features/{ticker}_qlib_features.csv"
        df.to_csv(feature_path)
        print(f"✓ Qlib alpha features compiled and archived to {feature_path}")
        return df

    def compute_predictive_score(self, df: pd.DataFrame) -> float:
        """
        Executes a composite predictive heuristic calculation combining
        momentum and mean reversion factors to generate a single directional Alpha score.
        """
        latest_row = df.iloc[-1]

        # Composite logic: positive momentum combined with buying support near moving average
        alpha_score = (latest_row['qlib_momentum_5d'] * 0.4) + (latest_row['qlib_mean_reversion_20d'] * 0.6)
        return float(alpha_score)
