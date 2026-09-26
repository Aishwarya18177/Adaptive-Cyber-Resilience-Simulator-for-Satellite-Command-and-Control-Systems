from collections import deque


class JammingDetector:

    def __init__(self, window_size=5):
        self.history = deque(maxlen=window_size)

    def analyze(self, telemetry):

        self.history.append({
            "signal": telemetry["signal"],
            "uplink": telemetry["uplink"],
            "downlink": telemetry["downlink"]
        })

        if len(self.history) < 3:
            return {
                "detected": False,
                "type": "NONE",
                "confidence": 0,
                "severity": "LOW",
                "reason": "Insufficient telemetry history"
            }

        signal_drop = self.history[0]["signal"] - self.history[-1]["signal"]
        uplink_drop = self.history[0]["uplink"] - self.history[-1]["uplink"]
        downlink_drop = self.history[0]["downlink"] - self.history[-1]["downlink"]

        score = 0
        reasons = []

        if signal_drop > 5:
            score += 30
            reasons.append("Rapid signal degradation")

        if uplink_drop > 5:
            score += 25
            reasons.append("Uplink degradation")

        if downlink_drop > 5:
            score += 25
            reasons.append("Downlink degradation")

        if telemetry["communication"] == "DEGRADED":
            score += 20
            reasons.append("Communication link degraded")

        score = min(score, 100)

        if score >= 70:
            return {
                "detected": True,
                "type": "JAMMING",
                "confidence": score,
                "severity": "HIGH" if score >= 85 else "MEDIUM",
                "reason": reasons
            }

        if score >= 40:
            return {
                "detected": True,
                "type": "POSSIBLE JAMMING",
                "confidence": score,
                "severity": "MEDIUM",
                "reason": reasons
            }

        return {
            "detected": False,
            "type": "NONE",
            "confidence": score,
            "severity": "LOW",
            "reason": reasons
        }