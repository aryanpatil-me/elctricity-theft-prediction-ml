import pandas as pd


FEATURE_LIST = [
    "T1_CS",
    "T1_VS",
    "T2_CS",
    "T2_VS",
    "H1_CS",
    "H1_VS",
    "T1_T2_CS_diff",
    "T2_H1_CS_diff",
    "T1_H1_CS_diff",
    "T1_T2_VS_diff",
    "T2_H1_VS_diff",
    "T1_H1_VS_diff",
]


def create_model2_features(data):
    """
    Convert one ESP32 reading into the exact
    12 features used by Model 2.
    """

    required = [
        "T1_CS",
        "T1_VS",
        "T2_CS",
        "T2_VS",
        "H1_CS",
        "H1_VS",
    ]

    # Check required values
    for column in required:
        if column not in data:
            raise ValueError(f"Missing ESP32 value: {column}")

    # Create one-row dataframe
    X = pd.DataFrame([data])

    # Current difference features
    X["T1_T2_CS_diff"] = X["T1_CS"] - X["T2_CS"]
    X["T2_H1_CS_diff"] = X["T2_CS"] - X["H1_CS"]
    X["T1_H1_CS_diff"] = X["T1_CS"] - X["H1_CS"]

    # Voltage difference features
    X["T1_T2_VS_diff"] = X["T1_VS"] - X["T2_VS"]
    X["T2_H1_VS_diff"] = X["T2_VS"] - X["H1_VS"]
    X["T1_H1_VS_diff"] = X["T1_VS"] - X["H1_VS"]

    # IMPORTANT:
    # Force exactly the same feature order as training
    X = X[FEATURE_LIST]

    return X