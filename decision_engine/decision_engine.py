class AdaptiveDecisionEngine:

    def decide(
        self,
        threat,
        telemetry,
        mission_criticality="CRITICAL",
        command_security=None,
        defense_mode="adaptive"        # NEW: "adaptive" | "static_none" | "static_isolate_only"
    ):

        # =================================================
        # STATIC BASELINE MODES (for comparison testing)
        # =================================================

        if defense_mode == "static_none":
            return {
                "action": "NONE",
                "priority": "N/A",
                "reason": "Static baseline: no adaptive response configured.",
                "severity": threat.get("severity", "UNKNOWN"),
                "communication_health": None
            }

        if defense_mode == "static_isolate_only":
            if threat["detected"] or (command_security and (
                command_security.get("replay_detected") or command_security.get("spoof_detected")
            )):
                return {
                    "action": "ISOLATE",
                    "priority": "CRITICAL",
                    "reason": "Static baseline: any detected threat triggers full isolation.",
                    "severity": threat.get("severity", "UNKNOWN"),
                    "communication_health": None
                }
            return {
                "action": "NONE",
                "priority": "N/A",
                "reason": "Static baseline: no threat detected.",
                "severity": "NONE",
                "communication_health": None
            }

        # =================================================
        # COMMAND SECURITY HAS HIGHEST PRIORITY (unchanged, adaptive mode)
        # =================================================

        if command_security:
            replay_detected = command_security.get("replay_detected", False)
            spoof_detected = command_security.get("spoof_detected", False)

            if replay_detected:
                return {
                    "action": "ISOLATE",
                    "priority": "CRITICAL",
                    "reason": (
                        "Replay attack detected in the satellite command channel. "
                        "Isolate the affected command path to prevent unauthorized "
                        "command execution."
                    ),
                    "severity": "CRITICAL",
                    "communication_health": None
                }

            if spoof_detected:
                return {
                    "action": "ISOLATE",
                    "priority": "CRITICAL",
                    "reason": (
                        "Spoofed command detected from an unauthorized source. "
                        "Isolate the affected command path."
                    ),
                    "severity": "CRITICAL",
                    "communication_health": None
                }

        if not threat["detected"]:
            return {
                "action": "NONE",
                "priority": "NORMAL",
                "reason": "No active threat detected",
                "severity": "NONE",
                "communication_health": None
            }

        severity = threat["severity"]
        signal = telemetry["signal"]
        uplink = telemetry["uplink"]
        downlink = telemetry["downlink"]
        communication_health = (signal + uplink + downlink) / 3

        if severity == "HIGH" and communication_health > 60:
            return {
                "action": "ADAPT_LINK",
                "priority": "HIGH",
                "reason": (
                    "Jamming detected while communication remains usable "
                    f"(health={communication_health:.1f}%). Adaptive link protection "
                    "is activated to preserve mission operations instead of a full "
                    "disruptive response."
                ),
                "severity": severity,
                "communication_health": round(communication_health, 1)
            }

        if severity == "HIGH" and communication_health <= 60:
            return {
                "action": "THROTTLE",
                "priority": "HIGH",
                "reason": (
                    f"Communication degradation is significant (health="
                    f"{communication_health:.1f}%, below 60% usability threshold). "
                    "Reduce non-critical traffic to preserve mission-critical "
                    "communication rather than fully isolating."
                ),
                "severity": severity,
                "communication_health": round(communication_health, 1)
            }

        if severity == "CRITICAL":
            return {
                "action": "ISOLATE",
                "priority": "CRITICAL",
                "reason": "Threat severity is critical. Isolate the affected communication path.",
                "severity": severity,
                "communication_health": round(communication_health, 1)
            }

        if severity == "MEDIUM":
            return {
                "action": "MONITOR",
                "priority": "MEDIUM",
                "reason": "Threat requires increased monitoring without disrupting normal mission operations.",
                "severity": severity,
                "communication_health": round(communication_health, 1)
            }

        return {
            "action": "MONITOR",
            "priority": "LOW",
            "reason": "Continue monitoring the anomaly.",
            "severity": severity,
            "communication_health": round(communication_health, 1)
        }