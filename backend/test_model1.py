import joblib

from model1_features import create_model1_features


# Load Model 1
model = joblib.load(
    "project/models/isolation_forest_final.joblib"
)


# --------------------------------------------------
# Temporary test consumption history
# --------------------------------------------------

consumption_history = [
    100,
    105,
    98,
    110,
    102,
    108,
    115,
    103,
    107,
    111,
    109,
    118,
    105,
    112,
    108,
    115,
    120,
    110,
    114,
    119,
    116,
    121,
    117,
    125,
    122,
    128,
    124,
    130,
    126,
    132
]


# Create the 7 features
features = create_model1_features(
    consumption_history
)


print("\nModel 1 features:")
print(features.to_string(index=False))


# Prediction
prediction = model.predict(features)[0]

print("\nRaw Model 1 prediction:", prediction)


if prediction == 1:
    print("Model 1 result: NORMAL")
elif prediction == -1:
    print("Model 1 result: SUSPICIOUS")
else:
    print("Model 1 result: UNKNOWN")