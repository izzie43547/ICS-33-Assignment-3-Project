import pytest
from pathlib import Path
from typing import List, Dict, Any, Tuple
from rules import detect_violations

# Test data
def create_scenario(
    max_speed: float = 30.0,
    min_follow: float = 5.0,
    stop_wait: float = 3.0,
    speed_zones: List[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Helper to create a scenario dictionary."""
    if speed_zones is None:
        speed_zones = []
    return {
        "road_rules": {
            "max_speed": max_speed,
            "min_follow_distance": min_follow,
            "stop_sign_wait": stop_wait
        },
        "speed_zones": speed_zones
    }

# Test cases for SPEEDING violation
def test_speeding_over_global_limit():
    """Test that speeding over global limit is detected."""
    scenario = create_scenario(max_speed=30.0)
    events = [
        (0.0, "SPEED", "31.0"),  # Should trigger SPEEDING
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 1
    assert violations[0]["type"] == "SPEEDING"
    assert "31.0 mph in 30 mph zone" in violations[0]["details"]

def test_speeding_exact_limit():
    """Test that speed exactly at the limit is not considered speeding."""
    scenario = create_scenario(max_speed=30.0)
    events = [
        (0.0, "SPEED", "30.0"),  # Exactly at limit, should NOT be speeding
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 0, "Speed exactly at limit should not be a violation"

def test_speeding_in_speed_zone():
    """Test that speeding in a speed zone is detected."""
    scenario = create_scenario(
        max_speed=35.0,
        speed_zones=[{"start_mile": 0.0, "end_mile": 1.0, "speed_limit": 25.0}]
    )
    events = [
        (0.0, "SPEED", "26.0"),  # Should trigger SPEEDING in zone
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 1
    assert violations[0]["type"] == "SPEEDING"
    assert "26.0 mph in 25 mph zone" in violations[0]["details"]

# Test cases for TAILGATING violation
def test_tailgating_detected():
    """Test that tailgating is detected."""
    scenario = create_scenario(min_follow=5.0)
    events = [
        (0.0, "FOLLOW_DISTANCE", "4.9"),  # Should trigger TAILGATING
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 1
    assert violations[0]["type"] == "TAILGATING"
    assert "4.9 m < 5.0 m" in violations[0]["details"]

def test_tailgating_boundary():
    """Test that exactly at min_follow_distance is not tailgating."""
    scenario = create_scenario(min_follow=5.0)
    events = [
        (0.0, "FOLLOW_DISTANCE", "5.0"),  # Should NOT trigger TAILGATING
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 0

# Test cases for ROLLING_STOP violation
def test_rolling_stop_detected():
    """Test that rolling stop is detected."""
    scenario = create_scenario(stop_wait=3.0)
    events = [
        (0.0, "STOP_SIGN_DETECTED", ""),
        (1.0, "SPEED", "0.0"),
        (2.0, "SPEED", "2.0"),  # Accelerated before waiting 3s
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 1
    assert violations[0]["type"] == "ROLLING_STOP"
    assert "Stopped 2.0s; required 3.0s" in violations[0]["details"]

def test_safe_stop_no_violation():
    """Test that proper stop doesn't trigger violation."""
    scenario = create_scenario(stop_wait=3.0)
    events = [
        (0.0, "STOP_SIGN_DETECTED", ""),
        (1.0, "SPEED", "0.0"),
        (2.0, "SPEED", "0.0"),
        (3.0, "SPEED", "0.0"),
        (4.0, "SPEED", "2.0"),  # Waited 4s (>3s) before accelerating
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 0

# Test cases for UNSAFE_LANE_CHANGE violation
def test_unsafe_lane_change_after_close_follow():
    """Test unsafe lane change after close follow."""
    scenario = create_scenario(min_follow=5.0)
    events = [
        (0.0, "FOLLOW_DISTANCE", "4.9"),  # Too close
        (1.0, "LANE_CHANGE", "LEFT"),     # Unsafe lane change
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 2  # Should include both TAILGATING and UNSAFE_LANE_CHANGE
    assert any(v["type"] == "UNSAFE_LANE_CHANGE" for v in violations)
    assert any("follow 4.9 m < 5.0 m" in v["details"] for v in violations)

def test_no_unsafe_lane_change_when_far():
    """Test no unsafe lane change when following at safe distance."""
    scenario = create_scenario(min_follow=5.0)
    events = [
        (0.0, "FOLLOW_DISTANCE", "5.1"),  # Safe distance
        (1.0, "LANE_CHANGE", "LEFT"),     # Should be safe
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 0

def test_ordering_of_violations_is_time_non_decreasing():
    """Test that violations are reported in non-decreasing time order."""
    scenario = create_scenario(max_speed=30.0, min_follow=5.0)
    events = [
        (10.0, "SPEED", "35.0"),          # SPEEDING at 10s
        (5.0, "FOLLOW_DISTANCE", "4.0"),  # TAILGATING at 5s
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 2
    # Should be ordered by time even though events were out of order
    assert violations[0]["time"] <= violations[1]["time"]
    assert "TAILGATING" in violations[0]["type"] or "TAILGATING" in violations[1]["type"]
    assert "SPEEDING" in violations[0]["type"] or "SPEEDING" in violations[1]["type"]

def test_no_false_positive_on_normal_driving():
    """Test no violations are reported for normal driving."""
    scenario = create_scenario(max_speed=35.0, min_follow=5.0, stop_wait=3.0)
    events = [
        (0.0, "SPEED", "30.0"),
        (1.0, "FOLLOW_DISTANCE", "6.0"),
        (2.0, "LANE_CHANGE", "LEFT"),
        (3.0, "STOP_SIGN_DETECTED", ""),
        (4.0, "SPEED", "0.0"),
        (5.0, "SPEED", "0.0"),
        (6.0, "SPEED", "0.0"),  # Waited 3s
        (7.0, "SPEED", "5.0"),   # Then accelerated
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 0

def test_multiple_speeding_violations():
    """Test multiple speeding violations are detected."""
    scenario = create_scenario(max_speed=30.0)
    events = [
        (0.0, "SPEED", "35.0"),
        (1.0, "SPEED", "25.0"),
        (2.0, "SPEED", "40.0"),
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 2
    assert all(v["type"] == "SPEEDING" for v in violations)
    assert any("35.0 mph" in v["details"] for v in violations)
    assert any("40.0 mph" in v["details"] for v in violations)

def test_stop_sign_ignored_if_speed_never_drops():
    """Test that stop sign is ignored if speed never drops below 1mph."""
    scenario = create_scenario(stop_wait=3.0)
    events = [
        (0.0, "STOP_SIGN_DETECTED", ""),
        (1.0, "SPEED", "2.0"),  # Never fully stopped
        (2.0, "SPEED", "5.0"),
    ]
    violations = detect_violations(scenario, events)
    assert len(violations) == 0  # No rolling stop violation if never fully stopped