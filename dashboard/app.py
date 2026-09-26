import sys
import time
from collections import deque
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))  # so metrics/ is importable
from metrics.scenario_run import compare_modes


SATELLITE_API = "http://127.0.0.1:8001"


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="SAT-01 Cyber-Resilience Mission Control",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# CUSTOM UI STYLE
# =========================================================

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .main-header { padding: 1.2rem 1.5rem; border-radius: 12px; border: 1px solid rgba(128,128,128,0.25); margin-bottom: 1rem; }
    .main-header h1 { margin-bottom: 0.2rem; }
    .main-header p { margin-top: 0; opacity: 0.75; }
    .section-title { font-size: 1.35rem; font-weight: 700; margin-top: 0.5rem; margin-bottom: 0.7rem; }
    .security-safe { padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(0, 180, 90, 0.45); margin-bottom: 1rem; }
    .security-danger { padding: 1.2rem; border-radius: 12px; border: 2px solid rgba(220, 50, 50, 0.65); margin-bottom: 1rem; }
    .security-warning { padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(230, 160, 0, 0.55); margin-bottom: 1rem; }
    .security-title { font-size: 1.25rem; font-weight: 800; }
    .security-subtitle { opacity: 0.8; margin-top: 0.3rem; }
    .defense-card { padding: 1rem; border-radius: 10px; border: 1px solid rgba(128,128,128,0.3); min-height: 85px; }
    .defense-active { border: 2px solid rgba(0, 180, 100, 0.65); }
    .defense-danger { border: 2px solid rgba(220, 50, 50, 0.65); }
    .small-label { font-size: 0.8rem; opacity: 0.65; text-transform: uppercase; letter-spacing: 0.08em; }
    .attack-panel { padding: 1rem; border-radius: 12px; border: 1px solid rgba(220, 60, 60, 0.35); }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="main-header">
    <h1>🛰️ SAT-01 — Cyber-Resilience Mission Control</h1>
    <p>Adaptive Cyber-Resilience Simulator | Satellite Command & Control Security</p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

if "history" not in st.session_state:
    st.session_state.history = deque(maxlen=40)

if "sequence" not in st.session_state:
    st.session_state.sequence = 1


# =========================================================
# GET SATELLITE TELEMETRY
# =========================================================

try:
    response = requests.get(f"{SATELLITE_API}/telemetry", timeout=1)
    response.raise_for_status()
    data = response.json()
    satellite_online = True
except requests.RequestException:
    satellite_online = False
    data = None


if not satellite_online:
    st.error("🔴 SATELLITE CONNECTION LOST")
    st.write("Ground station cannot communicate with SAT-01.")
    st.stop()


st.success("🟢 SATELLITE OPERATIONAL — LIVE TELEMETRY LINK ACTIVE")


# =========================================================
# TELEMETRY HISTORY
# =========================================================

st.session_state.history.append({
    "time": data["timestamp"],
    "Signal": data["signal"],
    "Uplink": data["uplink"],
    "Downlink": data["downlink"]
})


# =========================================================
# TELEMETRY CARDS
# =========================================================

st.markdown('<div class="section-title">📊 Live Satellite Telemetry</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📡 Signal", f"{data['signal']:.1f}%")
col2.metric("⬆️ Uplink", f"{data['uplink']:.1f}%")
col3.metric("⬇️ Downlink", f"{data['downlink']:.1f}%")
col4.metric("🌡️ Temperature", f"{data['temperature']:.1f} °C")
col5.metric("🔋 Battery", f"{data['battery']:.1f}%")

st.divider()


# =========================================================
# TELEMETRY + MISSION
# =========================================================

left, right = st.columns([2.2, 1])

with left:
    st.markdown('<div class="section-title">📡 Communication Telemetry</div>', unsafe_allow_html=True)

    df = pd.DataFrame(list(st.session_state.history))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["time"], y=df["Signal"], mode="lines+markers", name="Signal"))
    fig.add_trace(go.Scatter(x=df["time"], y=df["Uplink"], mode="lines+markers", name="Uplink"))
    fig.add_trace(go.Scatter(x=df["time"], y=df["Downlink"], mode="lines+markers", name="Downlink"))

    fig.update_layout(
        height=420,
        yaxis_title="Health %",
        xaxis_title="Time",
        yaxis_range=[0, 100],
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h")
    )

    st.plotly_chart(fig, width="stretch")


with right:
    st.markdown('<div class="section-title">🛰️ Mission Status</div>', unsafe_allow_html=True)
    st.info(f"**Mission**\n\n{data['mission']}")
    st.metric("Communication", data["communication"])
    st.write("**Security Architecture**")
    st.write("🧠 Detection Engine")
    st.write("⚙️ Adaptive Decision Engine")
    st.write("🛡️ Automated Response")
    st.caption(f"Last telemetry: {data['timestamp']}")


# =========================================================
# GET ATTACK STATUS
# =========================================================

try:
    attack_status_response = requests.get(f"{SATELLITE_API}/attack/status", timeout=1)
    attack_status_response.raise_for_status()
    attack_status = attack_status_response.json()
except requests.RequestException:
    attack_status = {}

jamming_active = attack_status.get("jamming", False)
replay_active = attack_status.get("command_replay", False)
spoof_active = attack_status.get("command_spoofing", False)


# =========================================================
# GET COMMAND SECURITY STATUS
# =========================================================

try:
    security_response = requests.get(f"{SATELLITE_API}/command/security-status", timeout=1)
    security_response.raise_for_status()
    security = security_response.json()
except requests.RequestException:
    security = {}

replay_detected = security.get("replay_detected", False)
spoof_detected = security.get("spoof_detected", False)
blocked_commands = security.get("blocked_commands", 0)
last_security_event = security.get("last_security_event", "NONE")


# =========================================================
# GET RESPONSE STATUS
# =========================================================

try:
    response_status_response = requests.get(f"{SATELLITE_API}/response/status", timeout=1)
    response_status_response.raise_for_status()
    response_state = response_status_response.json()
except requests.RequestException:
    response_state = {}

adaptive_link = response_state.get("adaptive_link", False)
throttle = response_state.get("throttle", False)
isolated = response_state.get("isolated", False)
command_block = response_state.get("command_block", False)


# =========================================================
# SECURITY INCIDENT PANEL
# =========================================================

st.divider()
st.markdown('<div class="section-title">🚨 Security Incident Monitor</div>', unsafe_allow_html=True)

if replay_detected or replay_active:
    st.markdown(
        f"""
        <div class="security-danger">
        <div class="security-title">🚨 COMMAND REPLAY DETECTED</div>
        <div class="security-subtitle">Unauthorized reuse of a previously accepted command detected.</div>
        <br>
        <b>Severity:</b> CRITICAL<br>
        <b>Confidence:</b> 100%<br>
        <b>Status:</b> REPLAYED COMMAND BLOCKED<br>
        <b>Blocked Commands:</b> {blocked_commands}<br>
        <b>Last Event:</b> {last_security_event}
        </div>
        """,
        unsafe_allow_html=True
    )

elif spoof_detected or spoof_active:
    st.markdown(
        f"""
        <div class="security-danger">
        <div class="security-title">🚨 COMMAND SPOOFING DETECTED</div>
        <div class="security-subtitle">Suspicious command source detected.</div>
        <br>
        <b>Severity:</b> CRITICAL<br>
        <b>Status:</b> SPOOFED COMMAND BLOCKED<br>
        <b>Blocked Commands:</b> {blocked_commands}
        </div>
        """,
        unsafe_allow_html=True
    )

elif jamming_active and (adaptive_link or throttle or isolated):
    defense_name = "ACTIVE DEFENSE"
    if adaptive_link:
        defense_name = "ADAPTIVE LINK PROTECTION"
    elif throttle:
        defense_name = "TRAFFIC THROTTLING"
    elif isolated:
        defense_name = "COMMUNICATION ISOLATION"

    st.markdown(
        f"""
        <div class="security-warning">
        <div class="security-title">⚠️ JAMMING DETECTED — MITIGATION ACTIVE</div>
        <div class="security-subtitle">Cyber attack remains active while the resilience system is reducing its operational impact.</div>
        <br>
        <b>Defense:</b> {defense_name}<br>
        <b>Communication:</b> {data['communication']}
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.markdown(
        """
        <div class="security-safe">
        <div class="security-title">🟢 SYSTEM SECURE</div>
        <div class="security-subtitle">No active cyber threat detected. Satellite mission operations are continuing normally.</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# NEW: DECISION REASONING PANEL
# =========================================================

st.divider()
st.markdown('<div class="section-title">🧠 Adaptive Decision Reasoning</div>', unsafe_allow_html=True)

try:
    decision_response = requests.get(f"{SATELLITE_API}/decision/status", timeout=1)
    decision_response.raise_for_status()
    decision_data = decision_response.json()

    dcol1, dcol2, dcol3 = st.columns(3)
    dcol1.metric("Action Taken", decision_data.get("action", "NONE"))
    dcol2.metric("Priority", decision_data.get("priority", "N/A"))
    comm_health = decision_data.get("communication_health")
    dcol3.metric("Comm Health at Decision", f"{comm_health:.1f}%" if comm_health is not None else "N/A")

    st.info(f"**Why:** {decision_data.get('reason', 'No decision yet.')}")
    st.caption(f"Last updated: {decision_data.get('timestamp', 'N/A')}")

except requests.RequestException:
    st.warning("Decision engine status unavailable.")


# =========================================================
# NEW: DEFENSE MODE CONTROL
# =========================================================

st.divider()
st.markdown('<div class="section-title">⚙️ Defense Mode</div>', unsafe_allow_html=True)

try:
    mode_response = requests.get(f"{SATELLITE_API}/config/defense-mode", timeout=1)
    current_mode = mode_response.json().get("mode", "adaptive")
except requests.RequestException:
    current_mode = "adaptive"

mode_options = ["adaptive", "static_none", "static_isolate_only"]
selected_mode = st.selectbox(
    "Engine mode (switch to generate baseline comparison data)",
    mode_options,
    index=mode_options.index(current_mode)
)

if selected_mode != current_mode:
    try:
        requests.post(f"{SATELLITE_API}/config/defense-mode", params={"mode": selected_mode}, timeout=1)
        st.success(f"Defense mode set to {selected_mode}")
        time.sleep(0.3)
        st.rerun()
    except requests.RequestException as error:
        st.error(f"Failed to set mode: {error}")


# =========================================================
# NEW: RESILIENCE COMPARISON
# =========================================================

st.divider()
st.markdown('<div class="section-title">📊 Resilience Comparison — Adaptive vs Static</div>', unsafe_allow_html=True)

comparison_scenario = st.selectbox("Scenario to compare", ["jamming", "replay", "spoofing"])
comparison = compare_modes(comparison_scenario)

if not comparison:
    st.info("No runs recorded yet for this scenario. Trigger some attacks in each defense mode to build comparison data.")
else:
    modes_present = list(comparison.keys())
    scores = [comparison[m]["avg_resilience_score"] for m in modes_present]
    continuity = [comparison[m]["avg_continuity_ratio"] * 100 for m in modes_present]

    comp_fig = go.Figure()
    comp_fig.add_trace(go.Bar(x=modes_present, y=scores, name="Resilience Score"))
    comp_fig.add_trace(go.Bar(x=modes_present, y=continuity, name="Continuity %"))
    comp_fig.update_layout(
        barmode="group", height=350,
        yaxis_title="Score / %",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h")
    )
    st.plotly_chart(comp_fig, width="stretch")

    for mode in modes_present:
        st.caption(
            f"**{mode}**: {comparison[mode]['count']} runs · "
            f"avg score {comparison[mode]['avg_resilience_score']} · "
            f"avg continuity {comparison[mode]['avg_continuity_ratio']*100:.0f}% · "
            f"avg recovery {comparison[mode]['avg_recovery_latency']}s"
        )


# =========================================================
# GROUND STATION COMMAND CENTER
# =========================================================

st.divider()
st.markdown('<div class="section-title">🌍 Ground Station — Command Center</div>', unsafe_allow_html=True)

command_col1, command_col2 = st.columns(2)

with command_col1:
    target = st.selectbox("Target Subsystem", ["CAMERA", "COMMUNICATION", "ATTITUDE", "POWER", "TELEMETRY"])

with command_col2:
    actions = {
        "CAMERA": ["CAPTURE_IMAGE", "STOP_CAMERA"],
        "COMMUNICATION": ["RESET_LINK", "ENABLE_BACKUP_LINK"],
        "ATTITUDE": ["ROTATE_LEFT", "ROTATE_RIGHT"],
        "POWER": ["POWER_STATUS"],
        "TELEMETRY": ["REQUEST_STATUS"]
    }
    action = st.selectbox("Command", actions[target])

if st.button("🚀 SEND COMMAND", width="stretch"):
    command = {
        "command_id": f"CMD-{st.session_state.sequence:04d}",
        "sequence": st.session_state.sequence,
        "source": "GROUND-STATION",
        "target": target,
        "action": action
    }

    try:
        command_response = requests.post(f"{SATELLITE_API}/command", json=command, timeout=2)
        command_response.raise_for_status()
        result = command_response.json()

        if result.get("status") == "ACCEPTED":
            st.session_state.sequence += 1
            st.success(f"✓ Command {result['command_id']} accepted")
            st.json(result)
        elif result.get("status") == "BLOCKED":
            st.error("🚫 COMMAND BLOCKED")
            st.json(result)
        else:
            st.warning("Command response received.")
            st.json(result)

    except requests.RequestException as error:
        st.error(f"Command delivery failed: {error}")


# =========================================================
# LAST COMMAND
# =========================================================

st.divider()
st.markdown('<div class="section-title">📋 Last Command</div>', unsafe_allow_html=True)

try:
    command_response = requests.get(f"{SATELLITE_API}/last-command", timeout=1)
    command_response.raise_for_status()
    last_command = command_response.json()

    if last_command.get("command_id"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Command ID", last_command["command_id"])
        c2.metric("Sequence", last_command["sequence"])
        c3.metric("Status", last_command["status"])
        st.write(f"**Target:** `{last_command['target']}`")
        st.write(f"**Action:** `{last_command['action']}`")
        st.write(f"**Source:** `{last_command['source']}`")
    else:
        st.info("No commands have been sent yet.")

except requests.RequestException:
    st.warning("Unable to retrieve command information.")


# =========================================================
# ATTACK SIMULATOR
# =========================================================

st.divider()
st.markdown('<div class="section-title">⚔️ Attack Simulator</div>', unsafe_allow_html=True)
st.caption("Controlled cybersecurity attack simulation for testing the satellite resilience engine.")

st.write("**📡 Communication Jamming**")
jamming_col1, jamming_col2 = st.columns(2)

with jamming_col1:
    if st.button("📡 START JAMMING", width="stretch"):
        try:
            response = requests.post(f"{SATELLITE_API}/attack/jamming/start", timeout=2)
            response.raise_for_status()
            st.error("🔴 JAMMING ATTACK STARTED")
            time.sleep(0.5)
            st.rerun()
        except requests.RequestException as error:
            st.error(f"Unable to start jamming: {error}")

with jamming_col2:
    if st.button("🛑 STOP JAMMING", width="stretch"):
        try:
            response = requests.post(f"{SATELLITE_API}/attack/jamming/stop", timeout=2)
            response.raise_for_status()
            st.success("🟢 JAMMING STOPPED")
            time.sleep(0.5)
            st.rerun()
        except requests.RequestException as error:
            st.error(f"Unable to stop jamming: {error}")


st.write("**🔁 Command Replay Attack**")
st.caption("Send a legitimate command first, then replay the last accepted command.")
replay_col1, replay_col2 = st.columns(2)

with replay_col1:
    if st.button("🔁 SIMULATE COMMAND REPLAY", width="stretch"):
        try:
            response = requests.post(f"{SATELLITE_API}/attack/command-replay", timeout=2)
            response.raise_for_status()
            result = response.json()

            if result.get("status") == "ACTIVE":
                st.error("🔴 COMMAND REPLAY ATTACK TRIGGERED")
                replay_result = result.get("result")
                if replay_result:
                    if replay_result.get("status") == "BLOCKED":
                        st.error("🚫 REPLAYED COMMAND BLOCKED")
                    st.json(replay_result)
            else:
                st.warning(result.get("message", "Replay attack could not be started."))

            time.sleep(0.5)
            st.rerun()

        except requests.RequestException as error:
            st.error(f"Unable to start command replay: {error}")

with replay_col2:
    if st.button("🛡️ RESET COMMAND DEFENSE", width="stretch"):
        try:
            attack_response = requests.post(f"{SATELLITE_API}/attack/command-stop", timeout=2)
            attack_response.raise_for_status()
            reset_response = requests.post(f"{SATELLITE_API}/response/reset", timeout=2)
            reset_response.raise_for_status()
            st.success("🟢 Command attack and defense reset.")
            time.sleep(0.5)
            st.rerun()
        except requests.RequestException as error:
            st.error(f"Unable to reset command defense: {error}")


# =========================================================
# LIVE ATTACK STATUS
# =========================================================

st.divider()
st.markdown('<div class="section-title">🚨 Live Attack Status</div>', unsafe_allow_html=True)

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    if jamming_active:
        st.error("🔴 JAMMING ACTIVE")
    else:
        st.success("🟢 JAMMING CLEAR")

with status_col2:
    if replay_active:
        st.error("🔴 COMMAND REPLAY ACTIVE")
    else:
        st.success("🟢 REPLAY CLEAR")

with status_col3:
    if spoof_active:
        st.error("🔴 COMMAND SPOOFING ACTIVE")
    else:
        st.success("🟢 SPOOFING CLEAR")


# =========================================================
# COMMAND SECURITY
# =========================================================

st.divider()
st.markdown('<div class="section-title">🔐 Command Security</div>', unsafe_allow_html=True)

security_col1, security_col2, security_col3 = st.columns(3)
security_col1.metric("Last Security Event", last_security_event)
security_col2.metric("Blocked Commands", blocked_commands)
security_col3.metric("Last Accepted Sequence", security.get("last_sequence", 0))


# =========================================================
# DEFENSE RESPONSE
# =========================================================

st.divider()
st.markdown('<div class="section-title">🛡️ Active Defense Response</div>', unsafe_allow_html=True)

defense_col1, defense_col2, defense_col3, defense_col4 = st.columns(4)

with defense_col1:
    if adaptive_link:
        st.success("🛡️ ADAPTIVE LINK\n\nACTIVE")
    else:
        st.info("Adaptive Link\n\nINACTIVE")

with defense_col2:
    if throttle:
        st.warning("⚠️ TRAFFIC THROTTLING\n\nACTIVE")
    else:
        st.info("Traffic Throttling\n\nINACTIVE")

with defense_col3:
    if isolated:
        st.error("🔴 COMMUNICATION ISOLATED\n\nACTIVE")
    else:
        st.info("Communication Isolation\n\nINACTIVE")

with defense_col4:
    if command_block:
        st.error("🚫 COMMAND BLOCK\n\nACTIVE")
    elif replay_detected:
        st.warning("🚫 COMMAND BLOCK\n\nTRIGGERED")
    else:
        st.info("Command Block\n\nINACTIVE")


# =========================================================
# FOOTER
# =========================================================

st.divider()
st.caption("SAT-01 Cyber-Resilience Simulator | Adaptive Defense • Mission Continuity • Command Security")


# =========================================================
# AUTO REFRESH
# =========================================================

time.sleep(1)
st.rerun()
