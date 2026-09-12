import pandas as pd
import numpy as np

# Load hardware data
df = pd.read_csv("project/data/hardware_dataset.csv")

print("\nColumns:")
print(df.columns.tolist())

print("\nNumber of readings:", len(df))

print("\nFirst 5 readings:")
print(df.head())

# --------------------------------------------------
# 1. Calculate household power proxy
# --------------------------------------------------

df["H1_power"] = df["H1_VS"] * df["H1_CS"]

print("\nH1 power statistics:")
print(df["H1_power"].describe())

# --------------------------------------------------
# 2. Check H1 values
# --------------------------------------------------

print("\nH1 Voltage statistics:")
print(df["H1_VS"].describe())

print("\nH1 Current statistics:")
print(df["H1_CS"].describe())

# --------------------------------------------------
# 3. Check for invalid values
# --------------------------------------------------

print("\nMissing values:")
print(df[["H1_VS", "H1_CS", "H1_power"]].isna().sum())

print("\nZero H1 power readings:")
print((df["H1_power"] == 0).sum())

# --------------------------------------------------
# 4. Display the consumption sequence
# --------------------------------------------------

consumption = df["H1_power"].dropna().to_numpy()

print("\nConsumption sequence length:", len(consumption))

print("\nFirst 20 consumption values:")
print(consumption[:20])