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

    TODO(student):
      1) Extract and float() max_speed, min_follow_distance, stop_sign_wait.
      2) Iterate events in order; track:
         * last_follow (float|None),
         * stop_detect_time (float|None),
         * optionally last_speed (float).
      3) For SPEED:
           - check SPEEDING,
           - if stop_detect_time is not None and speed > 1.0 and t > stop_detect_time:
               compute waited = t - stop_detect_time;
               if waited < stop_wait -> add ROLLING_STOP;
               then clear stop_detect_time.
      4) For FOLLOW_DISTANCE: update last_follow; check TAILGATING.
      5) For LANE_CHANGE: if last_follow is set and < min_follow -> UNSAFE_LANE_CHANGE.
      6) When adding a violation, format time via _fmt_time(t).
      7) Sort by v["time"] and return.

    """
    raise NotImplementedError("TODO: implement detect_violations()")
