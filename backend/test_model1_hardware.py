import pandas as pd
import numpy as np
import joblib

from model1_features import create_model1_features


# =========================================================
# 1. LOAD ESP32 DATA
# =========================================================

df = pd.read_csv("project/data/hardware_dataset.csv")

print("Total ESP32 readings:", len(df))


# =========================================================
# 2. PROTOTYPE SENSOR CALIBRATION
# =========================================================

CURRENT_OFF_RMS_ADC = 15.41
CURRENT_40W_RMS_ADC = 49.40

REFERENCE_POWER_W = 40.0
REFERENCE_VOLTAGE_V = 230.0

REFERENCE_CURRENT_A = (
    REFERENCE_POWER_W / REFERENCE_VOLTAGE_V
)

CURRENT_SIGNAL_ADC = (
    CURRENT_40W_RMS_ADC -
    CURRENT_OFF_RMS_ADC
)

CURRENT_A_PER_ADC = (
    REFERENCE_CURRENT_A /
    CURRENT_SIGNAL_ADC
)

VOLTAGE_RMS_ADC_REFERENCE = 499.5

VOLTAGE_V_PER_ADC = (
    REFERENCE_VOLTAGE_V /
    VOLTAGE_RMS_ADC_REFERENCE
)


print("\nPrototype calibration:")
print(
    "Current calibration factor:",
    CURRENT_A_PER_ADC,
    "A/ADC"
)

print(
    "Voltage calibration factor:",
    VOLTAGE_V_PER_ADC,
    "V/ADC"
)


# =========================================================
# 3. CREATE HOUSE LOAD SIGNAL
# =========================================================

current_raw = df["H1_CS"].astype(float)

current_baseline = current_raw.median()

current_signal_adc = (
    current_raw - current_baseline
).abs()

# Convert ADC signal to approximate current
current_A = (
    current_signal_adc *
    CURRENT_A_PER_ADC
)

current_A = current_A.clip(lower=0)


# Voltage is approximately 230 V
voltage_V = np.full(
    len(df),
    REFERENCE_VOLTAGE_V
)


# =========================================================
# 4. APPROXIMATE POWER
# =========================================================

df["current_A"] = current_A
df["voltage_V"] = voltage_V

df["power_W"] = (
    df["current_A"] *
    df["voltage_V"]
)


print("\nEstimated electrical values:")

print(
    df[
        ["current_A", "voltage_V", "power_W"]
    ].describe()
)


# =========================================================
# 5. CREATE 30-DAY LOAD PROFILE
# =========================================================
#
# IMPORTANT:
#
# We are NOT using the short ESP32 recording duration
# as real elapsed energy.
#
# Instead, we preserve the relative load pattern and
# compress the observation into 30 simulated days.
#


NUM_DAYS = 30

power_chunks = np.array_split(
    df["power_W"].to_numpy(),
    NUM_DAYS
)


daily_power = []

for chunk in power_chunks:

    if len(chunk) == 0:
        daily_power.append(0)

    else:
        daily_power.append(
            np.mean(chunk)
        )


daily_power = np.array(
    daily_power,
    dtype=float
)


# =========================================================
# 6. CONVERT LOAD PROFILE TO DAILY CONSUMPTION
# =========================================================
#
# We use the relative variation of the measured load.
#
# Prototype reference:
# average household consumption = 5 kWh/day
#

PROTOTYPE_DAILY_KWH = 5.0

profile_mean = daily_power.mean()

if profile_mean > 0:

    daily_consumption_kwh = (
        daily_power /
        profile_mean
    ) * PROTOTYPE_DAILY_KWH

else:

    daily_consumption_kwh = np.zeros(
        NUM_DAYS
    )


# Safety: consumption cannot be negative
daily_consumption_kwh = np.clip(
    daily_consumption_kwh,
    0,
    None
)


# =========================================================
# 7. DISPLAY 30-DAY PROFILE
# =========================================================

print(
    "\n30-day prototype consumption history (kWh):"
)

for day, value in enumerate(
    daily_consumption_kwh,
    start=1
):

    print(
        f"Day {day:02d}: {value:.3f} kWh"
    )


print(
    "\nAverage daily consumption:",
    daily_consumption_kwh.mean()
)


# =========================================================
# 8. CREATE MODEL 1 FEATURES
# =========================================================

features = create_model1_features(
    daily_consumption_kwh
)


print("\nModel 1 features:")

print(
    features.to_string(
        index=False
    )
)


# =========================================================
# 9. LOAD MODEL 1
# =========================================================

model = joblib.load(
    "project/models/isolation_forest_final.joblib"
)


# =========================================================
# 10. PREDICTION
# =========================================================

prediction = model.predict(
    features
)[0]


print(
    "\nRaw Model 1 prediction:",
    prediction
)


if prediction == 1:

    print(
        "Model 1 result: NORMAL"
    )

elif prediction == -1:

    print(
        "Model 1 result: SUSPICIOUS"
    )

else:

    print(
        "Model 1 result: UNKNOWN"
    )