# =========================================================
# SIH - FINAL DECISION LOGIC
# =========================================================

def get_final_status(model1_result, model2_result):

    model1_result = str(model1_result).upper()
    model2_result = str(model2_result).upper()

    # -----------------------------------------------------
    # MODEL 2 FAULT S1
    # -----------------------------------------------------

    if model2_result == "FAULT_S1":

        if model1_result == "SUSPICIOUS":

            return {
                "final_status": "HIGH PRIORITY ALERT",
                "fault_type": "FAULT_S1",
                "priority": "CRITICAL",
                "message":
                    "Abnormal consumption pattern and S1 fault detected."
            }

        return {
            "final_status": "FAULT DETECTED",
            "fault_type": "FAULT_S1",
            "priority": "HIGH",
            "message":
                "S1 fault detected by real-time monitoring."
        }

    # -----------------------------------------------------
    # MODEL 2 FAULT S2
    # -----------------------------------------------------

    if model2_result == "FAULT_S2":

        if model1_result == "SUSPICIOUS":

            return {
                "final_status": "HIGH PRIORITY ALERT",
                "fault_type": "FAULT_S2",
                "priority": "CRITICAL",
                "message":
                    "Abnormal consumption pattern and S2 fault detected."
            }

        return {
            "final_status": "FAULT DETECTED",
            "fault_type": "FAULT_S2",
            "priority": "HIGH",
            "message":
                "S2 fault detected by real-time monitoring."
        }

    # -----------------------------------------------------
    # GENERIC FAULT
    # -----------------------------------------------------

    if model2_result == "FAULT":

        if model1_result == "SUSPICIOUS":

            return {
                "final_status": "HIGH PRIORITY ALERT",
                "fault_type": "ELECTRICAL_FAULT",
                "priority": "CRITICAL",
                "message":
                    "Abnormal consumption pattern and electrical fault detected."
            }

        return {
            "final_status": "FAULT DETECTED",
            "fault_type": "ELECTRICAL_FAULT",
            "priority": "HIGH",
            "message":
                "Electrical fault detected by real-time monitoring."
        }

    # -----------------------------------------------------
    # MODEL 1 SUSPICIOUS ONLY
    # -----------------------------------------------------

    if model1_result == "SUSPICIOUS":

        return {
            "final_status": "SUSPICIOUS",
            "fault_type": None,
            "priority": "MEDIUM",
            "message":
                "Abnormal consumption pattern detected."
        }

    # -----------------------------------------------------
    # NORMAL
    # -----------------------------------------------------

    return {
        "final_status": "NORMAL",
        "fault_type": None,
        "priority": "LOW",
        "message":
            "No abnormal condition detected."
    }