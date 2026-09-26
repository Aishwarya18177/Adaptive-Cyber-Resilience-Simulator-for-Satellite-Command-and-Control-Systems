import random
import asyncio
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn


app = FastAPI(title="Satellite Simulator")


# =========================================================
# SATELLITE TELEMETRY
# =========================================================

BASELINE = {"signal": 96.0, "uplink": 82.0, "downlink": 91.0}

telemetry = {
    "timestamp": "",
    "signal": BASELINE["signal"],
    "uplink": BASELINE["uplink"],
    "downlink": BASELINE["downlink"],
    "temperature": 41.5,
    "battery": 78.0,
    "communication": "NORMAL",
    "mission": "EARTH OBSERVATION"
}

command_history = []

last_command = {
    "command_id": None, "sequence": None, "timestamp": None,
    "source": None, "target": None, "action": None, "status": "NONE"
}

command_security = {
    "last_sequence": 0,
    "replay_detected": False,
    "spoof_detected": False,
    "blocked_commands": 0,
    "last_security_event": "NONE"
}


class Command(BaseModel):
    command_id: str
    sequence: int
    source: str
    target: str
    action: str


attack_state = {
    "jamming": False,
    "command_replay": False,
    "command_spoofing": False
}

response_state = {
    "adaptive_link": False,
    "throttle": False,
    "isolated": False,
    "command_block": False
}

# -----------------------------------------------------------
# NEW: shared defense-mode config, read/set by the engine loop
# and the dashboard, so both processes agree without restarts.
# -----------------------------------------------------------
defense_config = {
    "mode": "adaptive"   # "adaptive" | "static_none" | "static_isolate_only"
}

# -----------------------------------------------------------
# NEW: last decision made by the engine, pushed here so the
# dashboard can display the reasoning panel.
# -----------------------------------------------------------
last_decision = {
    "action": "NONE",
    "priority": "N/A",
    "reason": "System idle.",
    "severity": "NONE",
    "communication_health": None,
    "timestamp": None
}

# -----------------------------------------------------------
# NEW: legitimate-traffic counters, used for the real
# operational-continuity metric. Only counts commands sent
# through the normal /command endpoint as real ground-station
# traffic (is_synthetic_attack=False) — replay/spoof attack
# commands are excluded since those SHOULD be blocked and
# aren't a continuity failure.
# -----------------------------------------------------------
traffic_stats = {"sent": 0, "accepted": 0}


# =========================================================
# TELEMETRY GENERATION (unchanged)
# =========================================================

def generate_telemetry():
    if not attack_state["jamming"]:
        telemetry["signal"] = max(0, min(100, telemetry["signal"] + random.uniform(-0.8, 0.8)))
        telemetry["uplink"] = max(0, min(100, telemetry["uplink"] + random.uniform(-1.2, 1.2)))
        telemetry["downlink"] = max(0, min(100, telemetry["downlink"] + random.uniform(-1.0, 1.0)))
        telemetry["communication"] = "NORMAL"
    else:
        if response_state["isolated"]:
            telemetry["signal"] = max(20, telemetry["signal"] - random.uniform(0.2, 0.8))
            telemetry["uplink"] = max(15, telemetry["uplink"] - random.uniform(0.2, 0.8))
            telemetry["downlink"] = max(15, telemetry["downlink"] - random.uniform(0.2, 0.8))
            telemetry["communication"] = "ISOLATED"
        elif response_state["adaptive_link"]:
            telemetry["signal"] = max(60, min(90, telemetry["signal"] + random.uniform(-0.4, 0.8)))
            telemetry["uplink"] = max(50, min(82, telemetry["uplink"] + random.uniform(-0.4, 0.8)))
            telemetry["downlink"] = max(60, min(88, telemetry["downlink"] + random.uniform(-0.4, 0.8)))
            telemetry["communication"] = "ADAPTIVE_RECOVERY"
        elif response_state["throttle"]:
            telemetry["signal"] = max(45, min(80, telemetry["signal"] + random.uniform(-0.8, 0.5)))
            telemetry["uplink"] = max(40, min(72, telemetry["uplink"] + random.uniform(-0.6, 0.6)))
            telemetry["downlink"] = max(45, min(78, telemetry["downlink"] + random.uniform(-0.6, 0.6)))
            telemetry["communication"] = "THROTTLED"
        else:
            telemetry["signal"] = max(10, telemetry["signal"] - random.uniform(3.0, 6.0))
            telemetry["uplink"] = max(10, telemetry["uplink"] - random.uniform(4.0, 7.0))
            telemetry["downlink"] = max(10, telemetry["downlink"] - random.uniform(4.0, 7.0))
            telemetry["communication"] = "DEGRADED"

    telemetry["temperature"] += random.uniform(-0.15, 0.15)
    telemetry["battery"] = max(0, telemetry["battery"] - random.uniform(0.001, 0.01))
    telemetry["timestamp"] = datetime.now().strftime("%H:%M:%S")


async def telemetry_loop():
    while True:
        generate_telemetry()
        await asyncio.sleep(1)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telemetry_loop())


@app.get("/telemetry")
def get_telemetry():
    return telemetry


@app.get("/health")
def health():
    return {"status": "ONLINE", "satellite": "SAT-01"}


# =========================================================
# COMMAND API — now with real drop-under-attack behavior
# =========================================================

def _maybe_drop_for_active_defense() -> dict | None:
    """
    Returns a BLOCKED-style response dict if the current defense
    state should drop a legitimate command, else None.

    ISOLATE: link is fully cut — all commands blocked.
    THROTTLE: significant packet loss simulated — ~35% drop chance.
    ADAPT_LINK: minor residual instability — ~8% drop chance.
    """
    if response_state["isolated"]:
        return {"status": "BLOCKED", "security_event": "LINK_ISOLATED",
                "reason": "Communication path is isolated; no commands can be delivered."}
    if response_state["throttle"] and random.random() < 0.35:
        return {"status": "BLOCKED", "security_event": "THROTTLED_DROP",
                "reason": "Command dropped due to active traffic throttling under degraded link."}
    if response_state["adaptive_link"] and random.random() < 0.08:
        return {"status": "BLOCKED", "security_event": "ADAPTIVE_LINK_DROP",
                "reason": "Command dropped due to residual link instability during adaptive recovery."}
    return None


@app.post("/command")
def receive_command(command: Command, is_synthetic_attack: bool = False):

    if not is_synthetic_attack:
        traffic_stats["sent"] += 1

    command_security["replay_detected"] = False
    command_security["spoof_detected"] = False

    # ---- Replay detection (unchanged) ----
    if command.sequence <= command_security["last_sequence"]:
        command_security["replay_detected"] = True
        command_security["blocked_commands"] += 1
        command_security["last_security_event"] = "REPLAYED COMMAND BLOCKED"
        response_state["command_block"] = True
        return {
            "command_id": command.command_id, "sequence": command.sequence,
            "source": command.source, "target": command.target, "action": command.action,
            "status": "BLOCKED", "security_event": "REPLAY_DETECTED",
            "reason": "Command sequence number is not newer than the last accepted command."
        }

    # ---- Source validation (unchanged) ----
    allowed_sources = ["GROUND-STATION"]
    if command.source not in allowed_sources:
        command_security["spoof_detected"] = True
        command_security["blocked_commands"] += 1
        command_security["last_security_event"] = "SPOOFED COMMAND BLOCKED"
        response_state["command_block"] = True
        return {
            "command_id": command.command_id, "sequence": command.sequence,
            "source": command.source, "target": command.target, "action": command.action,
            "status": "BLOCKED", "security_event": "SPOOF_DETECTED",
            "reason": "Command source is not an authorized ground station."
        }

    # ---- NEW: drop check for legitimate commands under active defense ----
    if not is_synthetic_attack:
        drop = _maybe_drop_for_active_defense()
        if drop is not None:
            return {
                "command_id": command.command_id, "sequence": command.sequence,
                "source": command.source, "target": command.target, "action": command.action,
                **drop
            }

    # ---- Valid, accepted command ----
    command_security["last_sequence"] = command.sequence
    command_security["last_security_event"] = "VALID COMMAND ACCEPTED"
    response_state["command_block"] = False

    if not is_synthetic_attack:
        traffic_stats["accepted"] += 1

    command_record = {
        "command_id": command.command_id, "sequence": command.sequence,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "source": command.source, "target": command.target,
        "action": command.action, "status": "ACCEPTED"
    }
    command_history.append(command_record)
    last_command.update(command_record)
    return command_record


@app.get("/commands")
def get_commands():
    return command_history[-20:]


@app.get("/last-command")
def get_last_command():
    return last_command


@app.get("/command/security-status")
def command_security_status():
    return command_security


# =========================================================
# NEW: TRAFFIC STATS (for real continuity metric)
# =========================================================

@app.get("/traffic/status")
def traffic_status():
    return traffic_stats


@app.post("/traffic/reset")
def traffic_reset():
    traffic_stats["sent"] = 0
    traffic_stats["accepted"] = 0
    return {"status": "RESET"}


# =========================================================
# NEW: DEFENSE MODE CONFIG (adaptive vs static baselines)
# =========================================================

@app.get("/config/defense-mode")
def get_defense_mode():
    return defense_config


@app.post("/config/defense-mode")
def set_defense_mode(mode: str):
    if mode not in ("adaptive", "static_none", "static_isolate_only"):
        return {"status": "ERROR", "message": "Invalid mode"}
    defense_config["mode"] = mode
    return {"status": "OK", "mode": mode}


# =========================================================
# NEW: DECISION STATUS (engine pushes here, dashboard reads)
# =========================================================

@app.post("/decision/update")
def update_decision(decision: dict):
    last_decision.update(decision)
    last_decision["timestamp"] = datetime.now().strftime("%H:%M:%S")
    return {"status": "OK"}


@app.get("/decision/status")
def get_decision_status():
    return last_decision


# =========================================================
# ATTACKS
# =========================================================

@app.post("/attack/jamming/start")
def start_jamming():
    attack_state["jamming"] = True
    response_state["adaptive_link"] = False
    response_state["throttle"] = False
    response_state["isolated"] = False
    return {"attack": "JAMMING", "status": "ACTIVE"}


@app.post("/attack/jamming/stop")
def stop_jamming():
    attack_state["jamming"] = False
    response_state["adaptive_link"] = False
    response_state["throttle"] = False
    response_state["isolated"] = False
    telemetry["communication"] = "NORMAL"
    return {"attack": "JAMMING", "status": "STOPPED"}


@app.get("/attack/status")
def attack_status():
    return attack_state


@app.post("/attack/command-replay")
def start_command_replay():
    if last_command["command_id"] is None:
        return {"attack": "COMMAND_REPLAY", "status": "FAILED",
                "message": "No previously accepted command exists. Send a valid command first."}

    attack_state["command_replay"] = True
    attack_state["command_spoofing"] = False

    replayed_command = Command(
        command_id=last_command["command_id"], sequence=last_command["sequence"],
        source=last_command["source"], target=last_command["target"], action=last_command["action"]
    )
    result = receive_command(replayed_command, is_synthetic_attack=True)
    return {"attack": "COMMAND_REPLAY", "status": "ACTIVE", "message": "Replay attack executed.", "result": result}


@app.post("/attack/command-spoof")
def start_command_spoof():
    if last_command["command_id"] is None:
        return {"attack": "COMMAND_SPOOFING", "status": "FAILED", "message": "Send a valid command first."}

    attack_state["command_spoofing"] = True
    attack_state["command_replay"] = False

    spoofed_command = Command(
        command_id="SPOOF-0001", sequence=last_command["sequence"] + 1,
        source="UNKNOWN-SOURCE", target=last_command["target"], action=last_command["action"]
    )
    result = receive_command(spoofed_command, is_synthetic_attack=True)
    return {"attack": "COMMAND_SPOOFING", "status": "ACTIVE", "message": "Spoofed command executed.", "result": result}


@app.post("/attack/command-stop")
def stop_command_attack():
    attack_state["command_replay"] = False
    attack_state["command_spoofing"] = False
    response_state["command_block"] = False
    command_security["replay_detected"] = False
    command_security["spoof_detected"] = False
    command_security["last_security_event"] = "NONE"
    return {"attack": "COMMAND_ATTACK", "status": "STOPPED"}


# =========================================================
# RESPONSES
# =========================================================

@app.post("/response/adapt-link")
def adapt_link():
    response_state["adaptive_link"] = True
    response_state["throttle"] = False
    response_state["isolated"] = False
    return {"response": "ADAPT_LINK", "status": "ACTIVE", "message": "Communication link adaptation activated"}


@app.post("/response/throttle")
def throttle():
    response_state["throttle"] = True
    response_state["adaptive_link"] = False
    response_state["isolated"] = False
    return {"response": "THROTTLE", "status": "ACTIVE", "message": "Non-critical communication throttled"}


@app.post("/response/isolate")
def isolate():
    response_state["isolated"] = True
    response_state["adaptive_link"] = False
    response_state["throttle"] = False
    return {"response": "ISOLATE", "status": "ACTIVE", "message": "Affected communication path isolated"}


@app.post("/response/reset")
def reset_response():
    response_state["adaptive_link"] = False
    response_state["throttle"] = False
    response_state["isolated"] = False
    response_state["command_block"] = False
    command_security["replay_detected"] = False
    command_security["spoof_detected"] = False
    command_security["last_security_event"] = "NONE"
    attack_state["command_replay"] = False
    attack_state["command_spoofing"] = False
    # NOTE: traffic_stats is intentionally NOT reset here — the engine
    # loop reads and resets it explicitly at scenario-run boundaries
    # via /traffic/reset, so a run's continuity number reflects only
    # that run's window.
    return {"response": "RESET", "status": "NORMAL"}


@app.get("/response/status")
def response_status():
    return response_state


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)