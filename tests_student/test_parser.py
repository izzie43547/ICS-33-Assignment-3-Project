import json
import pytest
from pathlib import Path
from typing import Any, Dict, List, Tuple
import tempfile
import os

# Import the module to test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from parser import load_scenario, parse_time, read_log

# Test data
SAMPLE_SCENARIO = {
    "name": "Test Scenario",
    "road_rules": {
        "max_speed": 35.0,
        "min_follow_distance": 2.0,
        "stop_sign_wait": 3.0
    },
    "speed_zones": [
        {"start_mile": 0.0, "end_mile": 1.5, "speed_limit": 30.0},
        {"start_mile": 1.5, "end_mile": 3.0, "speed_limit": 25.0}
    ]
}

SAMPLE_SCENARIO_NO_ZONES = {
    "name": "Test Scenario No Zones",
    "road_rules": {
        "max_speed": 35.0,
        "min_follow_distance": 2.0,
        "stop_sign_wait": 3.0
    }
}

SAMPLE_LOG_LINES = [
    "0:00.5 SPEED 32.5\n",
    "0:01.0 FOLLOW_DISTANCE 1.8\n",
    "0:02.5 LANE_CHANGE LEFT\n",
    "0:03.0 STOP_SIGN_DETECTED\n"
]


class TestParseTime:
    """Test the parse_time function."""
    
    def test_parse_time_valid(self):
        """Test parsing valid time strings."""
        assert parse_time("0:00.0") == 0.0
        assert parse_time("1:23.4") == 83.4
        assert parse_time("0:59.9") == 59.9
        assert parse_time("5:00.1") == 300.1
    
    def test_parse_time_invalid_format(self):
        """Test parsing invalid time formats."""
        with pytest.raises(ValueError):
            parse_time("1:60.0")  # Seconds too high
        with pytest.raises(ValueError):
            parse_time("-1:00.0")  # Negative minutes
        with pytest.raises(ValueError):
            parse_time("1:-10.0")  # Negative seconds
        with pytest.raises(ValueError):
            parse_time("1:00.999")  # Too many decimal places
        with pytest.raises(ValueError):
            parse_time("not a time")  # Not a time string


class TestLoadScenario:
    """Test the load_scenario function."""
    
    def test_load_scenario_valid(self, tmp_path):
        """Test loading a valid scenario file."""
        # Create a temporary scenario file
        scenario_file = tmp_path / "scenario.json"
        scenario_file.write_text(json.dumps(SAMPLE_SCENARIO))
        
        # Load and verify the scenario
        scenario = load_scenario(scenario_file)
        assert scenario["name"] == "Test Scenario"
        assert scenario["road_rules"]["max_speed"] == 35.0
        assert len(scenario["speed_zones"]) == 2
    
    def test_load_scenario_no_zones(self, tmp_path):
        """Test loading a scenario with no speed zones."""
        # Create a temporary scenario file with no speed_zones
        scenario_file = tmp_path / "scenario_no_zones.json"
        scenario_file.write_text(json.dumps(SAMPLE_SCENARIO_NO_ZONES))
        
        # Load and verify the scenario
        scenario = load_scenario(scenario_file)
        assert scenario["name"] == "Test Scenario No Zones"
        assert "speed_zones" in scenario
        assert scenario["speed_zones"] == []  # Should be empty list, not missing
    
    def test_load_scenario_missing_required(self, tmp_path):
        """Test loading a scenario with missing required fields."""
        # Missing road_rules
        scenario = {"name": "Invalid Scenario"}
        scenario_file = tmp_path / "invalid_scenario.json"
        scenario_file.write_text(json.dumps(scenario))
        
        with pytest.raises(ValueError, match="missing 'road_rules'"):
            load_scenario(scenario_file)
        
        # Missing required rule
        scenario = {
            "road_rules": {
                "max_speed": 35.0,
                "min_follow_distance": 2.0
                # Missing stop_sign_wait
            }
        }
        scenario_file.write_text(json.dumps(scenario))
        
        with pytest.raises(ValueError, match="missing key: stop_sign_wait"):
            load_scenario(scenario_file)


class TestReadLog:
    """Test the read_log function."""
    
    def test_read_log_valid(self, tmp_path):
        """Test reading a valid log file."""
        # Create a temporary log file
        log_file = tmp_path / "test.log"
        log_file.write_text("".join(SAMPLE_LOG_LINES))
        
        # Read and verify the log
        events = list(read_log(log_file))
        assert len(events) == 4
        
        # Check the first event (SPEED)
        time1, type1, arg1 = events[0]
        assert time1 == 0.5
        assert type1 == "SPEED"
        assert arg1 == "32.5"
        
        # Check the second event (FOLLOW_DISTANCE)
        time2, type2, arg2 = events[1]
        assert time2 == 1.0
        assert type2 == "FOLLOW_DISTANCE"
        assert arg2 == "1.8"
        
        # Check the third event (LANE_CHANGE)
        time3, type3, arg3 = events[2]
        assert time3 == 2.5
        assert type3 == "LANE_CHANGE"
        assert arg3 == "LEFT"
        
        # Check the fourth event (STOP_SIGN_DETECTED)
        time4, type4, arg4 = events[3]
        assert time4 == 3.0
        assert type4 == "STOP_SIGN_DETECTED"
        assert arg4 == ""
    
    def test_read_log_invalid_time(self, tmp_path):
        """Test reading a log file with an invalid time format."""
        log_file = tmp_path / "invalid_time.log"
        log_file.write_text("1:60.0 SPEED 30.0\n")  # Invalid time (seconds > 59)
        
        with pytest.raises(ValueError):
            list(read_log(log_file))
    
    def test_read_log_missing_file(self):
        """Test reading a non-existent log file."""
        with pytest.raises(FileNotFoundError):
            list(read_log(Path("nonexistent_file.log")))
    
    def test_read_log_empty_file(self, tmp_path):
        """Test reading an empty log file."""
        log_file = tmp_path / "empty.log"
        log_file.touch()  # Create empty file
        
        events = list(read_log(log_file))
        assert events == []  # Should return empty list, not raise