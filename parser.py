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

    Args:
        ts: Timestamp string in format 'M:SS' or 'M:SS.s'
        
    Returns:
        float: Total seconds
        
    Raises:
        ValueError: If the timestamp format is invalid
    """
    try:
        # Split into minutes and seconds parts
        parts = ts.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid time format: {ts}")
            
        minutes = int(parts[0])
        seconds = float(parts[1])
        
        # Validate ranges
        if minutes < 0 or seconds < 0 or seconds >= 60:
            raise ValueError(f"Time values out of range: {ts}")
            
        return minutes * 60 + seconds
        
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid time format: {ts}") from e


def read_log(path: Path) -> Iterator[Tuple[float, str, str]]:
    """
    Read a log file and yield (time_sec, event_type, event_arg) tuples.

    Each line in the log file has the format:
      TIMESTAMP EVENT_TYPE [ARGUMENT]

    Where:
      - TIMESTAMP is in MM:SS.s format (see parse_time).
      - EVENT_TYPE is one of: SPEED, FOLLOW_DISTANCE, LANE_CHANGE, STOP_SIGN_DETECTED.
      - ARGUMENT is optional and depends on the event type:
          * SPEED <float>           # speed in mph
          * FOLLOW_DISTANCE <float>  # distance in meters
          * LANE_CHANGE <direction>  # 'LEFT' or 'RIGHT'
          * STOP_SIGN_DETECTED       # no argument

    Yields:
      (time_sec: float, event_type: str, event_arg: str)
      - time_sec: parsed timestamp in seconds (float)
      - event_type: one of the EVENT_TYPE strings
      - event_arg: the rest of the line after EVENT_TYPE
      
    Raises:
        FileNotFoundError: If the log file doesn't exist
        ValueError: For malformed log lines
    """
    valid_events = {'SPEED', 'FOLLOW_DISTANCE', 'LANE_CHANGE', 'STOP_SIGN_DETECTED'}
    
    try:
        with open(path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                # Skip empty lines and comments
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                try:
                    # Split into parts
                    parts = line.split()
                    if len(parts) < 2:
                        raise ValueError(f"Line {line_num}: Invalid format")
                    
                    # Parse timestamp and event type
                    timestamp = parse_time(parts[0])
                    event_type = parts[1]
                    
                    # Validate event type
                    if event_type not in valid_events:
                        raise ValueError(f"Line {line_num}: Unknown event type: {event_type}")
                    
                    # Handle event arguments
                    event_arg = ''
                    if event_type in ('SPEED', 'FOLLOW_DISTANCE'):
                        if len(parts) != 3:
                            raise ValueError(f"Line {line_num}: {event_type} requires a numeric argument")
                        try:
                            float(parts[2])  # Validate it's a number
                        except ValueError:
                            raise ValueError(f"Line {line_num}: Invalid numeric value: {parts[2]}")
                        event_arg = parts[2]
                    elif event_type == 'LANE_CHANGE':
                        if len(parts) != 3 or parts[2] not in ('LEFT', 'RIGHT'):
                            raise ValueError(f"Line {line_num}: LANE_CHANGE requires 'LEFT' or 'RIGHT'")
                        event_arg = parts[2]
                    elif event_type == 'STOP_SIGN_DETECTED' and len(parts) != 2:
                        raise ValueError(f"Line {line_num}: STOP_SIGN_DETECTED takes no arguments")
                    
                    yield (timestamp, event_type, event_arg)
                    
                except ValueError as e:
                    raise ValueError(f"Error in log file '{path}', line {line_num}: {str(e)}")
                    
    except FileNotFoundError:
        raise FileNotFoundError(f"Log file not found: {path}")
