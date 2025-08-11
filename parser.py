from __future__ import annotations

from pathlib import Path
from typing import Iterator, Dict, Any, Tuple
import json


def load_scenario(path: Path) -> Dict[str, Any]:
    """
    Load a scenario JSON and validate required fields.

    Required:
      - top-level key "road_rules" (dict) with keys:
          * "max_speed"
          * "min_follow_distance"
          * "stop_sign_wait"
    Optional:
      - "speed_zones" (list), default to [] if missing.

    Returns:
        Dict containing the loaded and validated scenario data.
        
    Raises:
        FileNotFoundError: If the specified path doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        ValueError: If required fields are missing or have incorrect types.
    """
    # Load the JSON file
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Scenario file not found: {path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError("Invalid JSON in scenario file", e.doc, e.pos)
    
    # Validate road_rules
    if 'road_rules' not in data:
        raise ValueError("scenario missing 'road_rules'")
    
    road_rules = data['road_rules']
    required_rules = ['max_speed', 'min_follow_distance', 'stop_sign_wait']
    
    for rule in required_rules:
        if rule not in road_rules:
            raise ValueError(f"road_rules missing key: {rule}")
    
    # Ensure speed_zones exists and is a list
    data.setdefault('speed_zones', [])
    
    return data


def parse_time(ts: str) -> float:
    """
    Convert a timestamp like 'M:SS' or 'M:SS.s' into seconds (float).

    Examples:
      '0:05'   -> 5.0
      '1:02.5' -> 62.5

    TODO(student):
      1) Split minutes/seconds by ':'.
      2) Convert minutes to int, seconds to float.
      3) Return total seconds as minutes*60 + seconds.
      4) Raise ValueError for malformed inputs.
    """
    raise NotImplementedError("TODO: implement parse_time()")


def read_log(path: Path) -> Iterator[Tuple[float, str, str]]:
    """
    Parse a plaintext event log.

    Each non-empty line begins with a timestamp, then an event kind, optionally an argument.
    Allowed kinds and formats:
      - SPEED <float>
      - FOLLOW_DISTANCE <float>
      - LANE_CHANGE <LEFT|RIGHT>
      - STOP_SIGN_DETECTED        (no argument)

    Yields:
      (time_seconds: float, kind: str, arg: str)

    TODO(student):
      1) Open file and iterate lines; skip blank lines.
      2) Split into tokens; require at least [time, kind].
      3) Use parse_time() for the timestamp.
      4) Validate per-kind arity and argument value(s):
         * SPEED, FOLLOW_DISTANCE -> exactly 3 tokens; numeric third token.
         * LANE_CHANGE -> exactly 3 tokens; third token in {'LEFT','RIGHT'}.
         * STOP_SIGN_DETECTED -> exactly 2 tokens.
         * else -> raise ValueError(f"unknown kind: {kind}")
      5) On any malformed line, raise ValueError with a helpful message,
         e.g., ValueError(f"bad SPEED: {line!r}") or ValueError(f"bad line: {line!r}").
      6) Yield (t, kind, arg) where arg is '' when there is no argument.
    """
    raise NotImplementedError("TODO: implement read_log()")
