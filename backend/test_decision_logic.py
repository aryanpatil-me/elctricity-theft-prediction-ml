from decision_logic import get_final_status


test_cases = [
    ("NORMAL", "NORMAL"),
    ("SUSPICIOUS", "NORMAL"),
    ("NORMAL", "FAULT_S1"),
    ("NORMAL", "FAULT_S2"),
    ("SUSPICIOUS", "FAULT_S1"),
    ("SUSPICIOUS", "FAULT_S2"),
]


for model1, model2 in test_cases:

    result = get_final_status(
        model1,
        model2
    )

    print("\n----------------------------")

    print("Model 1:", model1)
    print("Model 2:", model2)
    print("Final:", result["final_status"])
    print("Priority:", result["priority"])

    if "fault_type" in result:
        print("Fault type:", result["fault_type"])

    print("Message:", result["message"])