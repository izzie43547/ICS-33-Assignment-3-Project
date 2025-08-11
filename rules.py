from __future__ import annotations
from typing import Dict, Any, Iterable, List, Tuple

Event = Tuple[float, str, str]


def _fmt_time(t: float) -> str:
    """
    Format seconds as MM:SS.s (zero-padded minutes, 1 decimal for seconds).
    Example: 62.5 -> "01:02.5"
    """
    m = int(t // 60)
    s = t - m * 60
    return f"{m:02d}:{s:04.1f}"


def detect_violations(scenario: Dict[str, Any], events: Iterable[Event]) -> List[Dict[str, str]]:
    """
    Apply rule checks to a stream of events.

    Road-rule inputs (scenario['road_rules']):
      - max_speed (mph, float-like)
      - min_follow_distance (meters, float-like)
      - stop_sign_wait (seconds, float-like)

    Event kinds (time: float seconds, kind: str, arg: str):
      - ("...", "SPEED", "<float mph>")
      - ("...", "FOLLOW_DISTANCE", "<float meters>")
      - ("...", "LANE_CHANGE", "LEFT" | "RIGHT")
      - ("...", "STOP_SIGN_DETECTED", "")

    Violations to emit (append dicts shaped as below):
      {"type": <str>, "time": <MM:SS.s>, "details": <str>}

    Required checks (use small epsilon like 1e-9 to avoid FP jitter):
      - SPEEDING when speed > max_speed
        details e.g.: f"{speed:.1f} mph in {max_speed:.0f} mph zone"
      - ROLLING_STOP after STOP_SIGN_DETECTED if the vehicle accelerates past ~1.0 mph
        before waiting stop_sign_wait seconds
        details e.g.: f"Stopped {waited:.1f}s; required {stop_wait:.1f}s"
      - TAILGATING when follow distance < min_follow
        details e.g.: f"{dist:.1f} m < {min_follow:.1f} m"
      - UNSAFE_LANE_CHANGE if a lane change occurs while follow distance < min_follow
        details e.g.: f"follow {dist:.1f} m < {min_follow:.1f} m"

    Ordering:
      - Sort the final list by the human-formatted "time" string.

    Returns:
        List of violation dictionaries, each with keys:
        - 'type': The type of violation (str)
        - 'time': Formatted timestamp (str)
        - 'details': Description of the violation (str)
        
    Raises:
        ValueError: If scenario is missing required road rules
      7) Sort by v["time"] and return.

    """
    raise NotImplementedError("TODO: implement detect_violations()")
