import numpy as np
import pandas as pd


MODEL1_FEATURES = [
    "mean_consumption",
    "median_consumption",
    "zero_days",
    "spike_ratio_filled",
    "p95_consumption",
    "consumption_trend",
    "median_zero",
]


def create_model1_features(consumption_history):
    """
    Create the exact 7 features used by Model 1.

    Parameters
    ----------
    consumption_history : list or array-like
        Sequential household consumption values.

    Returns
    -------
    pandas.DataFrame
        One-row DataFrame containing the 7 Model 1 features.
    """

    # Convert to pandas Series
    consumption = pd.Series(
        consumption_history,
        dtype="float64"
    )

    # Remove invalid values
    consumption = consumption.replace(
        [np.inf, -np.inf],
        np.nan
    )

    # Need at least 2 valid observations for the trend
    valid_count = consumption.notna().sum()

    # --------------------------------------------------
    # Same calculations as SGCC feature engineering
    # --------------------------------------------------

    mean_consumption = consumption.mean()

    median_consumption = consumption.median()

    zero_days = (consumption == 0).sum()

    max_consumption = consumption.max()

    if median_consumption > 0:
        spike_ratio = (
            max_consumption / median_consumption
        )
    else:
        spike_ratio = np.nan

    # Same logic as:
    # day_numbers = np.arange(len(consumption_cols))
    if valid_count >= 2:

        valid_values = consumption.dropna()

        day_numbers = np.arange(len(consumption))

        valid_mask = consumption.notna().to_numpy()

        consumption_trend = np.polyfit(
            day_numbers[valid_mask],
            valid_values.to_numpy(),
            1
        )[0]

    else:
        consumption_trend = np.nan

    p95_consumption = consumption.quantile(0.95)

    median_zero = int(
        median_consumption == 0
    )

    # Same as:
    # df["spike_ratio"].fillna(0)
    spike_ratio_filled = (
        0 if pd.isna(spike_ratio)
        else spike_ratio
    )

    # --------------------------------------------------
    # Final feature vector
    # --------------------------------------------------

    features = {
        "mean_consumption": mean_consumption,
        "median_consumption": median_consumption,
        "zero_days": zero_days,
        "spike_ratio_filled": spike_ratio_filled,
        "p95_consumption": p95_consumption,
        "consumption_trend": consumption_trend,
        "median_zero": median_zero,
    }

    return pd.DataFrame(
        [features],
        columns=MODEL1_FEATURES
    )