from detector import JammingDetector


detector = JammingDetector()


normal_values = [
    {
        "signal": 96,
        "uplink": 82,
        "downlink": 91,
        "communication": "NORMAL"
    },
    {
        "signal": 95.8,
        "uplink": 81.5,
        "downlink": 90.7,
        "communication": "NORMAL"
    },
    {
        "signal": 95.5,
        "uplink": 82.1,
        "downlink": 91.2,
        "communication": "NORMAL"
    }
]


for telemetry in normal_values:
    result = detector.analyze(telemetry)
    print(result)


jamming_values = [
    {
        "signal": 90,
        "uplink": 75,
        "downlink": 84,
        "communication": "DEGRADED"
    },
    {
        "signal": 82,
        "uplink": 66,
        "downlink": 75,
        "communication": "DEGRADED"
    },
    {
        "signal": 72,
        "uplink": 57,
        "downlink": 65,
        "communication": "DEGRADED"
    }
]


for telemetry in jamming_values:
    result = detector.analyze(telemetry)
    print(result)