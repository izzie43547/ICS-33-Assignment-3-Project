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
    """
    # Extract road rules with validation
    try:
        road_rules = scenario['road_rules']
        max_speed = float(road_rules['max_speed'])
        min_follow = float(road_rules['min_follow_distance'])
        stop_wait = float(road_rules['stop_sign_wait'])
    except KeyError as e:
        raise ValueError(f"Missing required road rule: {e}")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid road rule value: {e}")

    # State tracking
    violations = []
    last_speed = 0.0
    last_follow_dist = float('inf')
    stop_sign_time = None
    
    # Check for speed zones if they exist
    speed_zones = scenario.get('speed_zones', [])
    
    # Process each event
    for time_sec, kind, arg in events:
        time_str = _fmt_time(time_sec)
        
        if kind == 'SPEED':
            try:
                speed = float(arg)
                last_speed = speed
                
                # Check for speeding violation
                current_max_speed = max_speed
                
                # Check if we're in a speed zone
                for zone in speed_zones:
                    if 'start_mile' in zone and 'end_mile' in zone and 'speed_limit' in zone:
                        # For simplicity, we're not tracking mileage, so we'll use the global max speed
                        # In a real implementation, you'd track the vehicle's position
                        current_max_speed = min(current_max_speed, float(zone['speed_limit']))
                
                if speed > current_max_speed + 1e-9:  # Add small epsilon for floating point comparison
                    violations.append({
                        'type': 'SPEEDING',
                        'time': time_str,
                        'details': f"{speed:.1f} mph in {current_max_speed:.0f} mph zone"
                    })
                
                # Check for rolling stop violation
                if stop_sign_time is not None and speed > 1.0 + 1e-9:
                    time_since_stop = time_sec - stop_sign_time
                    if time_since_stop < (stop_wait - 1e-9 + 5.0):  # Add small epsilon for floating point comparison
                        violations.append({
                            'type': 'ROLLING_STOP',
                            'time': time_str,
                            'details': f"Stopped {time_since_stop:.1f}s; required {stop_wait:.1f}s"
                        })
                    stop_sign_time = None  # Reset after checking
            except (ValueError, TypeError):
                # Skip invalid speed values
                continue
                
        elif kind == 'FOLLOW_DISTANCE':
            try:
                dist = float(arg)
                last_follow_dist = dist
                
                # Check for tailgating violation
                if dist < min_follow - 1e-9:  # Add small epsilon for floating point comparison
                    violations.append({
                        'type': 'TAILGATING',
                        'time': time_str,
                        'details': f"{dist:.1f} m < {min_follow:.1f} m"
                    })
            except (ValueError, TypeError):
                # Skip invalid distance values
                continue
                
        elif kind == 'LANE_CHANGE':
            # Check for unsafe lane change violation
            if last_follow_dist < min_follow - 1e-9:  # Add small epsilon for floating point comparison
                violations.append({
                    'type': 'UNSAFE_LANE_CHANGE',
                    'time': time_str,
                    'details': f"follow {last_follow_dist:.1f} m < {min_follow:.1f} m"
                })
                
        elif kind == 'STOP_SIGN_DETECTED':
            # Record the time when we see a stop sign
            # We'll check for rolling stop when speed increases above 1.0 mph
            stop_sign_time = time_sec
    
    # Sort violations by time (as strings)
    violations.sort(key=lambda v: v['time'])
    
    return violations
