from decision_engine import AdaptiveDecisionEngine


engine = AdaptiveDecisionEngine()


threat = {
    "detected": True,
    "type": "JAMMING",
    "confidence": 92,
    "severity": "HIGH"
}


healthy_telemetry = {
    "signal": 88,
    "uplink": 78,
    "downlink": 85
}


degraded_telemetry = {
    "signal": 45,
    "uplink": 38,
    "downlink": 42
}


print("CASE 1 — Communication still usable")

print(
    engine.decide(
        threat,
        healthy_telemetry
    )
)


print("\nCASE 2 — Communication severely degraded")

print(
    engine.decide(
        threat,
        degraded_telemetry
    )
)