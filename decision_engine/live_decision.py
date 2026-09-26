import time
import requests

from detection.detector import JammingDetector
from decision_engine.decision_engine import AdaptiveDecisionEngine
from metrics.scenario_run import ScenarioRun


SATELLITE_API = "http://127.0.0.1:8001"

detector = JammingDetector()
decision_engine = AdaptiveDecisionEngine()

last_action = "NONE"
last_security_event = "NONE"

current_run: ScenarioRun | None = None


def get_defense_mode() -> str:
    try:
        r = requests.get(f"{SATELLITE_API}/config/defense-mode", timeout=1)
        r.raise_for_status()
        return r.json().get("mode", "adaptive")
    except requests.RequestException:
        return "adaptive"


def push_decision(decision: dict):
    try:
        requests.post(f"{SATELLITE_API}/decision/update", json=decision, timeout=1)
    except requests.RequestException:
        pass


def get_traffic_stats() -> dict:
    try:
        r = requests.get(f"{SATELLITE_API}/traffic/status", timeout=1)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return {"sent": 0, "accepted": 0}


def reset_traffic_stats():
    try:
        requests.post(f"{SATELLITE_API}/traffic/reset", timeout=1)
    except requests.RequestException:
        pass


def start_run_if_needed(scenario_name: str, defense_mode: str):
    global current_run
    if current_run is None:
        current_run = ScenarioRun.start(scenario_name, defense_mode=defense_mode)
        reset_traffic_stats()
        print(f"\n📊 [METRICS] Run started: {current_run.run_id} "
              f"({scenario_name}, mode={defense_mode})")


def end_run_if_active():
    global current_run
    if current_run is not None:
        stats = get_traffic_stats()
        sent, accepted = stats.get("sent", 0), stats.get("accepted", 0)
        # Record real legit-traffic outcomes (falls back to a neutral
        # 1/1 "no traffic attempted" case if nothing was sent this run,
        # handled automatically by continuity_ratio's default of 1.0).
        for _ in range(accepted):
            current_run.record_command(processed=True)
        for _ in range(sent - accepted):
            current_run.record_command(processed=False)

        current_run.mark_recovered()
        print(f"📊 [METRICS] Run ended: score={current_run.resilience_score} "
              f"continuity={current_run.continuity_ratio:.2f} "
              f"(legit traffic {accepted}/{sent})\n")
        current_run = None


def get_telemetry():
    r = requests.get(f"{SATELLITE_API}/telemetry", timeout=2)
    r.raise_for_status()
    return r.json()


def get_attack_status():
    r = requests.get(f"{SATELLITE_API}/attack/status", timeout=2)
    r.raise_for_status()
    return r.json()


def get_response_status():
    r = requests.get(f"{SATELLITE_API}/response/status", timeout=2)
    r.raise_for_status()
    return r.json()


def get_command_security_status():
    r = requests.get(f"{SATELLITE_API}/command/security-status", timeout=2)
    r.raise_for_status()
    return r.json()


def execute_response(action):
    endpoints = {"ADAPT_LINK": "/response/adapt-link", "THROTTLE": "/response/throttle", "ISOLATE": "/response/isolate"}
    endpoint = endpoints.get(action)
    if endpoint is None:
        return {"status": "NO_ACTION"}
    r = requests.post(f"{SATELLITE_API}{endpoint}", timeout=2)
    r.raise_for_status()
    return r.json()


def reset_defense():
    try:
        r = requests.post(f"{SATELLITE_API}/response/reset", timeout=2)
        r.raise_for_status()
        return True
    except requests.RequestException:
        return False


print("\n========================================")
print("       CYBER-RESILIENCE ENGINE")
print("========================================")

while True:
    try:
        telemetry = get_telemetry()
        attack = get_attack_status()
        response_state = get_response_status()
        command_security = get_command_security_status()
        defense_mode = get_defense_mode()

        jamming_active = attack.get("jamming", False)
        replay_detected = command_security.get("replay_detected", False)
        spoof_detected = command_security.get("spoof_detected", False)
        security_event = command_security.get("last_security_event", "NONE")

        detected_threat = detector.analyze(telemetry)

        if replay_detected:
            threat = {"detected": True, "type": "COMMAND REPLAY", "confidence": 100, "severity": "CRITICAL",
                      "reason": ["Replay attack detected", "Command sequence number reused"]}
        elif spoof_detected:
            threat = {"detected": True, "type": "COMMAND SPOOFING", "confidence": 100, "severity": "CRITICAL",
                      "reason": ["Unauthorized command source detected"]}
        elif jamming_active:
            threat = {"detected": True, "type": "JAMMING",
                      "confidence": max(detected_threat.get("confidence", 0), 90), "severity": "HIGH",
                      "reason": ["Jamming attack is active", "Communication degradation detected"]}
        else:
            threat = detected_threat

        incident_active = jamming_active or replay_detected or spoof_detected
        if incident_active:
            scenario_name = "replay" if replay_detected else "spoofing" if spoof_detected else "jamming"
            start_run_if_needed(scenario_name, defense_mode)

        if current_run is not None and threat["detected"]:
            current_run.mark_detected()

        decision = decision_engine.decide(
            threat, telemetry, mission_criticality="CRITICAL",
            command_security=command_security, defense_mode=defense_mode
        )
        action = decision["action"]

        if current_run is not None:
            current_run.mark_decided(action, decision["reason"])

        push_decision(decision)

        print(f"\nDECISION  action={action}  priority={decision['priority']}")
        print(f"Reason: {decision['reason']}")

        if action in ("ADAPT_LINK", "THROTTLE", "ISOLATE"):
            if action != last_action:
                result = execute_response(action)
                print(f"🛡️ Executed: {result}")
                last_action = action
                if current_run is not None:
                    current_run.mark_defense_action()

        if replay_detected or spoof_detected:
            if security_event != last_security_event:
                print(f"🚨 COMMAND SECURITY INCIDENT: {security_event}")
                last_security_event = security_event

        if not jamming_active:
            if last_action in ("ADAPT_LINK", "THROTTLE") and not replay_detected and not spoof_detected:
                print("🟢 JAMMING CLEARED")
                if reset_defense():
                    print("🛡️ Defense reset.")
                last_action = "NONE"
                end_run_if_active()

        if current_run is not None and current_run.scenario in ("replay", "spoofing"):
            if not replay_detected and not spoof_detected:
                end_run_if_active()

        print("================================")
        time.sleep(1)

    except requests.RequestException as error:
        print(f"\n⚠️ Satellite communication error: {error}")
        time.sleep(2)
    except KeyError as error:
        print(f"\n⚠️ Missing telemetry field: {error}")
        time.sleep(2)
    except Exception as error:
        print(f"\n⚠️ Engine error: {error}")
        time.sleep(2)