# =========================================================
# SIH SMART ELECTRICAL MONITORING BACKEND
#
# ESP32 -> WiFi -> Flask -> Model 1 + Model 2
#                         -> Temporal Filtering
#                         -> Fault Confirmation
#                         -> Decision Logic
#                         -> React Dashboard
# =========================================================

from flask import Flask, request, jsonify
from flask_cors import CORS

import joblib
import numpy as np

from collections import defaultdict, deque
from datetime import datetime

from model1_features import create_model1_features
from model2_features import create_model2_features
from decision_logic import get_final_status


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)

CORS(app)


# =========================================================
# MODELS
# =========================================================

MODEL1_PATH = "project/models/isolation_forest_final.joblib"
MODEL2_PATH = "project/models/sih_fault_detection_model_2.joblib"


print()
print("==========================================")
print("       SIH ML MODEL LOADING")
print("==========================================")

print("Loading Model 1...")

model1 = joblib.load(
    MODEL1_PATH
)

print("Model 1 loaded successfully!")

print("Loading Model 2...")

model2 = joblib.load(
    MODEL2_PATH
)

print("Model 2 loaded successfully!")

print("==========================================")
print()


# =========================================================
# CALIBRATION
# =========================================================

CURRENT_CALIBRATION_FACTOR = (
    0.005116594394770841
)

VOLTAGE_CALIBRATION_FACTOR = (
    0.46046046046046046
)

CURRENT_ZERO_ADC = 3000.0

REFERENCE_VOLTAGE = 230.0


# =========================================================
# METER LOCATIONS
# =========================================================

METER_LOCATIONS = {

    "M001": {
        "name": "Meter M001",
        "latitude": 21.2514,
        "longitude": 81.6296
    },

    "M002": {
        "name": "Meter M002",
        "latitude": 21.2550,
        "longitude": 81.6350
    },

    "M003": {
        "name": "Meter M003",
        "latitude": 21.2470,
        "longitude": 81.6220
    }

}


# =========================================================
# HISTORY
# =========================================================

meter_history = defaultdict(
    lambda: deque(maxlen=3000)
)


live_electrical_history = defaultdict(
    lambda: deque(maxlen=60)
)


latest_meter_data = {}


meter_last_seen = {}


# =========================================================
# MODEL 2 TEMPORAL FILTER
# =========================================================
#
# Raw predictions:
#
# NORMAL
# FAULT_S1
# FAULT_S2
#
# are stored here.
#
# =========================================================

model2_prediction_history = defaultdict(
    lambda: deque(maxlen=10)
)


# =========================================================
# FAULT STATE
# =========================================================
#
# This is the important part.
#
# Once a real fault is confirmed:
#
# FAULT_S1
# or
# FAULT_S2
#
# it remains ACTIVE until enough normal readings
# are received.
#
# =========================================================

fault_state = defaultdict(
    lambda: {

        "active": False,

        "fault_type": None,

        "fault_count": 0,

        "normal_count": 0,

        "confirmed_at": None,

        "last_fault_prediction": None

    }
)


# =========================================================
# FILTER SETTINGS
# =========================================================

PREDICTION_WINDOW = 10


# Number of fault predictions required inside
# the 10-reading window.

FAULT_CONFIRM_COUNT = 6


# Number of consecutive NORMAL readings required
# to clear a confirmed fault.

NORMAL_CLEAR_COUNT = 5


# =========================================================
# MODEL 1
# =========================================================

MODEL1_MIN_HISTORY = 30

PROTOTYPE_DAILY_KWH = 5.0


# =========================================================
# ELECTRICAL CALCULATION
# =========================================================

def calculate_electrical_values(
    h1_cs,
    h1_vs
):

    current_deviation = abs(
        float(h1_cs) -
        CURRENT_ZERO_ADC
    )


    current_a = (
        current_deviation *
        CURRENT_CALIBRATION_FACTOR
    )


    current_a = max(
        0.0,
        current_a
    )


    voltage_v = (
        REFERENCE_VOLTAGE
    )


    power_w = (
        voltage_v *
        current_a
    )


    return {

        "current_A":
            round(
                current_a,
                3
            ),

        "voltage_V":
            round(
                voltage_v,
                1
            ),

        "power_W":
            round(
                power_w,
                2
            ),

        "raw_current_adc":
            float(h1_cs),

        "raw_voltage_adc":
            float(h1_vs)

    }


# =========================================================
# LOCATION
# =========================================================

def get_meter_location(
    meter_id
):

    if meter_id in METER_LOCATIONS:

        return METER_LOCATIONS[
            meter_id
        ]


    return {

        "name":
            meter_id,

        "latitude":
            None,

        "longitude":
            None

    }


# =========================================================
# ONLINE
# =========================================================

def get_meter_online_status(
    meter_id
):

    if meter_id not in meter_last_seen:

        return False


    elapsed = (
        datetime.now() -
        meter_last_seen[meter_id]
    ).total_seconds()


    return elapsed <= 5


# =========================================================
# NORMALIZE MODEL 2 OUTPUT
# =========================================================

def normalize_model2_prediction(
    prediction
):

    prediction = str(
        prediction
    ).strip().upper()


    if prediction in [

        "NORMAL",

        "FAULT_S1",

        "FAULT_S2",

        "FAULT"

    ]:

        return prediction


    if prediction in [

        "1",

        "1.0"

    ]:

        return "NORMAL"


    if prediction in [

        "-1",

        "-1.0"

    ]:

        return "FAULT"


    return prediction


# =========================================================
# TEMPORAL FAULT FILTER
# =========================================================

def update_fault_filter(
    meter_id,
    raw_prediction
):

    state = fault_state[
        meter_id
    ]


    history = (
        model2_prediction_history[
            meter_id
        ]
    )


    # -----------------------------------------------------
    # Add prediction
    # -----------------------------------------------------

    history.append(
        raw_prediction
    )


    # -----------------------------------------------------
    # Current counts
    # -----------------------------------------------------

    normal_count = history.count(
        "NORMAL"
    )

    fault_s1_count = history.count(
        "FAULT_S1"
    )

    fault_s2_count = history.count(
        "FAULT_S2"
    )

    generic_fault_count = history.count(
        "FAULT"
    )


    # -----------------------------------------------------
    # Best specific fault
    # -----------------------------------------------------

    specific_fault = None

    specific_count = 0


    if fault_s1_count >= fault_s2_count:

        specific_fault = "FAULT_S1"

        specific_count = fault_s1_count

    else:

        specific_fault = "FAULT_S2"

        specific_count = fault_s2_count


    # -----------------------------------------------------
    # ACTIVE FAULT
    # -----------------------------------------------------

    if state["active"]:

        state["normal_count"] = (
            state["normal_count"] + 1
            if raw_prediction == "NORMAL"
            else 0
        )


        state["fault_count"] = (
            state["fault_count"] + 1
            if raw_prediction == state["fault_type"]
            else state["fault_count"]
        )


        # -------------------------------------------------
        # Clear only after 5 consecutive NORMAL readings
        # -------------------------------------------------

        if (
            state["normal_count"]
            >= NORMAL_CLEAR_COUNT
        ):

            print(
                f"[FAULT CLEARED] "
                f"{meter_id} -> "
                f"{state['fault_type']}"
            )


            state["active"] = False

            state["fault_type"] = None

            state["fault_count"] = 0

            state["normal_count"] = 0

            state["confirmed_at"] = None

            state["last_fault_prediction"] = None


            return {

                "prediction":
                    "NORMAL",

                "raw_prediction":
                    raw_prediction,

                "fault_active":
                    False,

                "fault_type":
                    None,

                "window_size":
                    len(history),

                "normal_count":
                    normal_count,

                "fault_s1_count":
                    fault_s1_count,

                "fault_s2_count":
                    fault_s2_count,

                "fault_confidence":
                    0.0,

                "fault_status":
                    "CLEARED"

            }


        # -------------------------------------------------
        # Keep confirmed fault
        # -------------------------------------------------

        return {

            "prediction":
                state["fault_type"],

            "raw_prediction":
                raw_prediction,

            "fault_active":
                True,

            "fault_type":
                state["fault_type"],

            "window_size":
                len(history),

            "normal_count":
                normal_count,

            "fault_s1_count":
                fault_s1_count,

            "fault_s2_count":
                fault_s2_count,

            "fault_confidence":
                round(
                    (
                        specific_count /
                        max(
                            1,
                            len(history)
                        )
                    ) * 100,
                    1
                ),

            "fault_status":
                "CONFIRMED"

        }


    # =====================================================
    # NO ACTIVE FAULT
    # =====================================================

    state["normal_count"] = (
        state["normal_count"] + 1
        if raw_prediction == "NORMAL"
        else 0
    )


    # -----------------------------------------------------
    # SPECIFIC FAULT CONFIRMATION
    # -----------------------------------------------------

    if (
        specific_count
        >= FAULT_CONFIRM_COUNT
    ):

        state["active"] = True

        state["fault_type"] = (
            specific_fault
        )

        state["fault_count"] = (
            specific_count
        )

        state["normal_count"] = 0

        state["confirmed_at"] = (
            datetime.now().isoformat()
        )

        state["last_fault_prediction"] = (
            raw_prediction
        )


        print(
            f"[FAULT CONFIRMED] "
            f"{meter_id} -> "
            f"{specific_fault}"
        )


        return {

            "prediction":
                specific_fault,

            "raw_prediction":
                raw_prediction,

            "fault_active":
                True,

            "fault_type":
                specific_fault,

            "window_size":
                len(history),

            "normal_count":
                normal_count,

            "fault_s1_count":
                fault_s1_count,

            "fault_s2_count":
                fault_s2_count,

            "fault_confidence":
                round(
                    (
                        specific_count /
                        max(
                            1,
                            len(history)
                        )
                    ) * 100,
                    1
                ),

            "fault_status":
                "CONFIRMED"

        }


    # -----------------------------------------------------
    # Generic FAULT
    # -----------------------------------------------------

    if (
        generic_fault_count
        >= FAULT_CONFIRM_COUNT
    ):

        state["active"] = True

        state["fault_type"] = (
            "ELECTRICAL_FAULT"
        )

        state["fault_count"] = (
            generic_fault_count
        )

        state["normal_count"] = 0

        state["confirmed_at"] = (
            datetime.now().isoformat()
        )


        return {

            "prediction":
                "ELECTRICAL_FAULT",

            "raw_prediction":
                raw_prediction,

            "fault_active":
                True,

            "fault_type":
                "ELECTRICAL_FAULT",

            "window_size":
                len(history),

            "normal_count":
                normal_count,

            "fault_s1_count":
                fault_s1_count,

            "fault_s2_count":
                fault_s2_count,

            "fault_confidence":
                round(
                    (
                        generic_fault_count /
                        max(
                            1,
                            len(history)
                        )
                    ) * 100,
                    1
                ),

            "fault_status":
                "CONFIRMED"

        }


    # =====================================================
    # STILL NORMAL / MONITORING
    # =====================================================

    return {

        "prediction":
            "NORMAL",

        "raw_prediction":
            raw_prediction,

        "fault_active":
            False,

        "fault_type":
            None,

        "window_size":
            len(history),

        "normal_count":
            normal_count,

        "fault_s1_count":
            fault_s1_count,

        "fault_s2_count":
            fault_s2_count,

        "fault_confidence":
            round(
                (
                    specific_count /
                    max(
                        1,
                        len(history)
                    )
                ) * 100,
                1
            ),

        "fault_status":
            "MONITORING"

    }


# =========================================================
# MODEL 1 CONSUMPTION
# =========================================================

def generate_model1_consumption(
    meter_id
):

    history = meter_history[
        meter_id
    ]


    if len(history) < MODEL1_MIN_HISTORY:

        return None


    values = np.array(
        history,
        dtype=float
    )


    baseline = np.median(
        values
    )


    signal = np.abs(
        values -
        baseline
    )


    if signal.mean() <= 0:

        return np.zeros(
            30
        )


    chunks = np.array_split(
        signal,
        30
    )


    daily_signal = []


    for chunk in chunks:

        if len(chunk) == 0:

            daily_signal.append(
                0.0
            )

        else:

            daily_signal.append(
                float(
                    np.mean(chunk)
                )
            )


    daily_signal = np.array(
        daily_signal,
        dtype=float
    )


    profile_mean = (
        daily_signal.mean()
    )


    if profile_mean <= 0:

        return np.zeros(
            30
        )


    consumption = (
        daily_signal /
        profile_mean
    ) * PROTOTYPE_DAILY_KWH


    consumption = np.clip(
        consumption,
        0,
        None
    )


    return consumption


# =========================================================
# MODEL 1
# =========================================================

def run_model1(
    meter_id
):

    consumption = (
        generate_model1_consumption(
            meter_id
        )
    )


    if consumption is None:

        return {

            "prediction":
                "WAITING",

            "raw_prediction":
                None,

            "history_length":
                len(
                    meter_history[
                        meter_id
                    ]
                ),

            "features":
                None,

            "consumption_history":
                None

        }


    features = (
        create_model1_features(
            consumption
        )
    )


    raw_prediction = (
        model1.predict(
            features
        )[0]
    )


    if raw_prediction == 1:

        prediction = "NORMAL"

    elif raw_prediction == -1:

        prediction = "SUSPICIOUS"

    else:

        prediction = "UNKNOWN"


    feature_dict = {}


    for column in features.columns:

        feature_dict[
            column
        ] = float(
            features.iloc[0][
                column
            ]
        )


    return {

        "prediction":
            prediction,

        "raw_prediction":
            int(
                raw_prediction
            ),

        "history_length":
            len(
                meter_history[
                    meter_id
                ]
            ),

        "features":
            feature_dict,

        "consumption_history": [

            round(
                float(value),
                3
            )

            for value
            in consumption

        ]

    }


# =========================================================
# HEALTH
# =========================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "status":
            "online",

        "model1_loaded":
            True,

        "model2_loaded":
            True,

        "meter_count":
            len(
                latest_meter_data
            )

    })


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({

        "status":
            "online",

        "service":
            "SIH Smart Electrical Monitoring Backend",

        "message":
            "Backend is running."

    })


# =========================================================
# RECEIVE ESP32 DATA
# =========================================================

@app.route(
    "/api/meter-data",
    methods=["POST"]
)
def receive_meter_data():

    try:

        data = request.get_json()


        if data is None:

            return jsonify({

                "status":
                    "error",

                "message":
                    "No JSON data received."

            }), 400


        meter_id = str(
            data.get(
                "meter_id",
                "M001"
            )
        )


        required_fields = [

            "T1_CS",
            "T1_VS",

            "T2_CS",
            "T2_VS",

            "H1_CS",
            "H1_VS"

        ]


        missing = [

            field

            for field
            in required_fields

            if field not in data

        ]


        if missing:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Missing sensor values.",

                "missing":
                    missing

            }), 400


        # =================================================
        # RAW READINGS
        # =================================================

        T1_CS = float(
            data["T1_CS"]
        )

        T1_VS = float(
            data["T1_VS"]
        )

        T2_CS = float(
            data["T2_CS"]
        )

        T2_VS = float(
            data["T2_VS"]
        )

        H1_CS = float(
            data["H1_CS"]
        )

        H1_VS = float(
            data["H1_VS"]
        )


        # =================================================
        # LAST SEEN
        # =================================================

        meter_last_seen[
            meter_id
        ] = datetime.now()


        # =================================================
        # ELECTRICAL VALUES
        # =================================================

        electrical = (
            calculate_electrical_values(
                H1_CS,
                H1_VS
            )
        )


        # =================================================
        # MODEL 1 HISTORY
        # =================================================

        meter_history[
            meter_id
        ].append(
            H1_CS
        )


        # =================================================
        # LIVE HISTORY
        # =================================================

        live_electrical_history[
            meter_id
        ].append({

            "time":
                data.get(
                    "time_ms",
                    0
                ),

            "current_A":
                electrical[
                    "current_A"
                ],

            "voltage_V":
                electrical[
                    "voltage_V"
                ],

            "power_W":
                electrical[
                    "power_W"
                ]

        })


        # =================================================
        # MODEL 2 FEATURES
        # =================================================

        model2_features = (
            create_model2_features(
                data
            )
        )


        # =================================================
        # MODEL 2 RAW
        # =================================================

        raw_model2 = (
            model2.predict(
                model2_features
            )[0]
        )


        raw_model2 = (
            normalize_model2_prediction(
                raw_model2
            )
        )


        # =================================================
        # TEMPORAL FILTER
        # =================================================

        filtered_model2 = (
            update_fault_filter(
                meter_id,
                raw_model2
            )
        )


        model2_result = (
            filtered_model2[
                "prediction"
            ]
        )


        # =================================================
        # MODEL 1
        # =================================================

        model1_result = (
            run_model1(
                meter_id
            )
        )


        # =================================================
        # FINAL DECISION
        # =================================================

        if (
            model1_result[
                "prediction"
            ]
            == "WAITING"
        ):

            decision = {

                "final_status":
                    "MONITORING",

                "fault_type":
                    filtered_model2[
                        "fault_type"
                    ],

                "priority":
                    "LOW",

                "message":
                    "Collecting consumption history for Model 1."

            }


        else:

            decision = (
                get_final_status(

                    model1_result[
                        "prediction"
                    ],

                    model2_result

                )
            )


        # =================================================
        # LOCATION
        # =================================================

        location = (
            get_meter_location(
                meter_id
            )
        )


        # =================================================
        # ONLINE
        # =================================================

        online = (
            get_meter_online_status(
                meter_id
            )
        )


        # =================================================
        # MODEL 2 FEATURES
        # =================================================

        model2_feature_dict = {}


        for column in model2_features.columns:

            model2_feature_dict[
                column
            ] = float(
                model2_features.iloc[0][
                    column
                ]
            )


        # =================================================
        # COMPLETE RESPONSE
        # =================================================

        response = {

            "status":
                "received",

            "meter_id":
                meter_id,

            "timestamp":
                data.get(
                    "time_ms"
                ),

            "server_time":
                datetime.now().isoformat(),

            "online":
                online,

            "location":
                location,

            "electrical":
                electrical,


            # =================================================
            # RAW SENSOR READINGS
            # =================================================

            "readings": {

                "T1_CS":
                    T1_CS,

                "T1_VS":
                    T1_VS,

                "T2_CS":
                    T2_CS,

                "T2_VS":
                    T2_VS,

                "H1_CS":
                    H1_CS,

                "H1_VS":
                    H1_VS

            },


            # =================================================
            # LIVE GRAPH
            # =================================================

            "live_history":
                list(
                    live_electrical_history[
                        meter_id
                    ]
                ),


            # =================================================
            # MODEL 1
            # =================================================

            "model1":
                model1_result,


            # =================================================
            # MODEL 2
            # =================================================

            "model2": {

                "prediction":
                    model2_result,

                "raw_prediction":
                    raw_model2,

                "fault_active":
                    filtered_model2[
                        "fault_active"
                    ],

                "fault_type":
                    filtered_model2[
                        "fault_type"
                    ],

                "fault_status":
                    filtered_model2[
                        "fault_status"
                    ],

                "fault_confidence":
                    filtered_model2[
                        "fault_confidence"
                    ],

                "window_size":
                    filtered_model2[
                        "window_size"
                    ],

                "normal_count":
                    filtered_model2[
                        "normal_count"
                    ],

                "fault_s1_count":
                    filtered_model2[
                        "fault_s1_count"
                    ],

                "fault_s2_count":
                    filtered_model2[
                        "fault_s2_count"
                    ],

                "smoothing_history_length":
                    len(
                        model2_prediction_history[
                            meter_id
                        ]
                    ),

                "features":
                    model2_feature_dict

            },


            # =================================================
            # FINAL DECISION
            # =================================================

            "decision":
                decision

        }


        # =================================================
        # SAVE
        # =================================================

        latest_meter_data[
            meter_id
        ] = response


        # =================================================
        # TERMINAL
        # =================================================

        print()
        print(
            "=========================================="
        )

        print(
            "Meter:",
            meter_id
        )

        print(
            "H1:",
            int(H1_CS),
            int(H1_VS)
        )

        print(
            "Raw Model 2:",
            raw_model2
        )

        print(
            "Model 2:",
            model2_result
        )

        print(
            "Fault active:",
            filtered_model2[
                "fault_active"
            ]
        )

        print(
            "Fault type:",
            filtered_model2[
                "fault_type"
            ]
        )

        print(
            "Fault confidence:",
            filtered_model2[
                "fault_confidence"
            ],
            "%"
        )

        print(
            "Model 1:",
            model1_result[
                "prediction"
            ]
        )

        print(
            "FINAL:",
            decision[
                "final_status"
            ]
        )

        print(
            "PRIORITY:",
            decision[
                "priority"
            ]
        )

        print(
            "=========================================="
        )


        return jsonify(
            response
        )


    except Exception as e:

        print()
        print(
            "BACKEND ERROR:"
        )

        print(
            str(e)
        )


        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# DASHBOARD
# =========================================================

@app.route(
    "/api/dashboard",
    methods=["GET"]
)
def dashboard():

    meters = []


    for meter_id, meter_data in (
        latest_meter_data.items()
    ):

        meter_copy = dict(
            meter_data
        )


        meter_copy[
            "online"
        ] = get_meter_online_status(
            meter_id
        )


        meter_copy[
            "location"
        ] = get_meter_location(
            meter_id
        )


        meters.append(
            meter_copy
        )


    return jsonify({

        "status":
            "online",

        "meter_count":
            len(meters),

        "meters":
            meters

    })


# =========================================================
# METERS
# =========================================================

@app.route(
    "/api/meters",
    methods=["GET"]
)
def get_meters():

    meters = []


    for meter_id in latest_meter_data:

        meters.append({

            "meter_id":
                meter_id,

            "online":
                get_meter_online_status(
                    meter_id
                ),

            "location":
                get_meter_location(
                    meter_id
                )

        })


    return jsonify({

        "status":
            "online",

        "meters":
            meters

    })


# =========================================================
# SINGLE METER
# =========================================================

@app.route(
    "/api/meter/<meter_id>",
    methods=["GET"]
)
def get_meter(
    meter_id
):

    if meter_id not in latest_meter_data:

        return jsonify({

            "status":
                "error",

            "message":
                "Meter not found."

        }), 404


    return jsonify(
        latest_meter_data[
            meter_id
        ]
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    print()
    print(
        "=========================================="
    )

    print(
        " SIH SMART ELECTRICAL MONITORING"
    )

    print(
        "=========================================="
    )

    print(
        "Backend:"
    )

    print(
        "http://192.168.1.5:5000"
    )

    print()

    print(
        "Dashboard API:"
    )

    print(
        "http://192.168.1.5:5000/api/dashboard"
    )

    print()

    print(
        "Health:"
    )

    print(
        "http://192.168.1.5:5000/api/health"
    )

    print(
        "=========================================="
    )


    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False

    )