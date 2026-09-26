
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


STORE_PATH = Path(__file__).parent / "runs.jsonl"

# Ceiling values used to normalize raw seconds into a 0-1 scale.
# Tune these once you see real timings from your system.
DETECTION_TIME_CEILING = 5.0    # seconds
DECISION_TIME_CEILING = 2.0     # seconds
RECOVERY_TIME_CEILING = 15.0    # seconds

# Weights for the composite resilience score (must sum to 1.0)
WEIGHTS = {
    "detection_speed": 0.20,
    "response_speed": 0.20,
    "continuity": 0.40,
    "recovery_speed": 0.20,
}


@dataclass
class ScenarioRun:
    run_id: str
    scenario: str                      # "jamming" | "replay" | "spoofing"
    defense_mode: str = "adaptive"     # "adaptive" | "static_none" | "static_isolate_only"

    attack_start: Optional[float] = None
    detection_time: Optional[float] = None
    decision_time: Optional[float] = None
    defense_action_time: Optional[float] = None
    recovery_time: Optional[float] = None

    defense_taken: str = "NONE"
    decision_reason: str = ""

    legit_commands_sent: int = 0
    legit_commands_processed: int = 0

    ended: bool = False

    @classmethod
    def start(cls, scenario: str, defense_mode: str = "adaptive") -> "ScenarioRun":
        return cls(
            run_id=str(uuid.uuid4()),
            scenario=scenario,
            defense_mode=defense_mode,
            attack_start=time.time(),
        )

    def mark_detected(self):
        if self.detection_time is None:
            self.detection_time = time.time()

    def mark_decided(self, action: str, reason: str):
        if self.decision_time is None:
            self.decision_time = time.time()
        self.defense_taken = action
        self.decision_reason = reason

    def mark_defense_action(self):
        if self.defense_action_time is None:
            self.defense_action_time = time.time()

    def mark_recovered(self):
        if self.recovery_time is None:
            self.recovery_time = time.time()
        self.ended = True
        self._persist()

    def record_command(self, processed: bool):
        self.legit_commands_sent += 1
        if processed:
            self.legit_commands_processed += 1

    # -----------------------------------------------------
    # Scoring
    # -----------------------------------------------------

    def _normalized(self, elapsed: Optional[float], ceiling: float) -> float:
        """Returns 1.0 = instant, 0.0 = at-or-beyond ceiling."""
        if elapsed is None or self.attack_start is None:
            return 0.0
        clamped = max(0.0, min(elapsed, ceiling))
        return 1.0 - (clamped / ceiling)

    @property
    def detection_latency(self) -> Optional[float]:
        if self.detection_time is None or self.attack_start is None:
            return None
        return self.detection_time - self.attack_start

    @property
    def decision_latency(self) -> Optional[float]:
        if self.decision_time is None or self.detection_time is None:
            return None
        return self.decision_time - self.detection_time

    @property
    def recovery_latency(self) -> Optional[float]:
        if self.recovery_time is None or self.attack_start is None:
            return None
        return self.recovery_time - self.attack_start

    @property
    def continuity_ratio(self) -> float:
        if self.legit_commands_sent == 0:
            return 1.0  # no legit traffic attempted, so nothing was disrupted
        return self.legit_commands_processed / self.legit_commands_sent

    @property
    def resilience_score(self) -> float:
        detection_component = self._normalized(
            self.detection_latency, DETECTION_TIME_CEILING
        )
        response_component = self._normalized(
            self.decision_latency, DECISION_TIME_CEILING
        )
        recovery_component = self._normalized(
            self.recovery_latency, RECOVERY_TIME_CEILING
        )
        continuity_component = self.continuity_ratio

        score = (
            WEIGHTS["detection_speed"] * detection_component
            + WEIGHTS["response_speed"] * response_component
            + WEIGHTS["continuity"] * continuity_component
            + WEIGHTS["recovery_speed"] * recovery_component
        )
        return round(score * 100, 1)  # 0-100 scale for display

    def to_dict(self) -> dict:
        d = asdict(self)
        d["detection_latency"] = self.detection_latency
        d["decision_latency"] = self.decision_latency
        d["recovery_latency"] = self.recovery_latency
        d["continuity_ratio"] = round(self.continuity_ratio, 3)
        d["resilience_score"] = self.resilience_score
        return d

    def _persist(self):
        with open(STORE_PATH, "a") as f:
            f.write(json.dumps(self.to_dict()) + "\n")


def load_runs(scenario: Optional[str] = None) -> list[dict]:
    """Load all persisted runs, optionally filtered by scenario name."""
    if not STORE_PATH.exists():
        return []
    runs = []
    with open(STORE_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if scenario is None or record["scenario"] == scenario:
                runs.append(record)
    return runs


def compare_modes(scenario: str) -> dict:
    """
    Returns average resilience score and continuity ratio for
    'adaptive' vs 'static_none' runs of the same scenario, so the
    dashboard can render a direct comparison.
    """
    runs = load_runs(scenario)
    result = {}
    for mode in ("adaptive", "static_none", "static_isolate_only"):
        mode_runs = [r for r in runs if r["defense_mode"] == mode]
        if not mode_runs:
            continue
        result[mode] = {
            "count": len(mode_runs),
            "avg_resilience_score": round(
                sum(r["resilience_score"] for r in mode_runs) / len(mode_runs), 1
            ),
            "avg_continuity_ratio": round(
                sum(r["continuity_ratio"] for r in mode_runs) / len(mode_runs), 3
            ),
            "avg_recovery_latency": round(
                sum(r["recovery_latency"] for r in mode_runs if r["recovery_latency"])
                / max(1, len([r for r in mode_runs if r["recovery_latency"]])),
                2,
            ),
        }
    return result