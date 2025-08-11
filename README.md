# Autonomous Vehicle Incident Log Analyzer

## Overview
This project implements an Autonomous Vehicle Incident Log Analyzer that processes driving logs, detects safety violations based on configurable rules, generates detailed reports, and stores the results in a SQLite database. The system is designed to help analyze and track safety incidents in autonomous vehicle test scenarios.

## Features
- **Log Parsing**: Read and parse log files containing vehicle telemetry data
- **Rule Engine**: Detect various types of safety violations based on configurable rules
- **Reporting**: Generate detailed violation reports
- **Persistence**: Store and query violation data in a SQLite database
- **CLI Interface**: Command-line interface for analyzing logs and querying the database

## Project Structure
```
.
├── parser.py          # Log file parsing and scenario loading
├── rules.py           # Safety rule definitions and violation detection
├── report.py          # Report generation
├── storage.py         # Database operations and persistence
├── log_analyzer.py    # Command-line interface
├── schema.sql         # Database schema definition
├── tests_student/     # Unit tests
│   ├── test_parser.py
│   ├── test_rules.py
│   ├── test_report.py
│   └── test_storage.py
└── README.md          # This file
```

## Installation
1. Clone the repository
2. Ensure you have Python 3.11+ installed
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Analyzing a Log File
```bash
python log_analyzer.py SCENARIO.json LOGFILE.txt [--db DATABASE.db]
```

Example:
```bash
python log_analyzer.py scenarios/city_driving.json logs/test_run_1.log --db violations.db
```

### Viewing Violation Summary
```bash
python log_analyzer.py --summary 10 --db DATABASE.db
```

### Querying Violations by Type
```bash
python log_analyzer.py --by-type SCENARIO_ID VIOLATION_TYPE --db DATABASE.db
```

Example:
```bash
python log_analyzer.py --by-type 1 SPEEDING --db violations.db
```

## Input Format

### Scenario File (JSON)
```json
{
  "name": "City Driving",
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
```

### Log File Format
```
MM:SS.s EVENT_TYPE [ARGUMENT]
```

Example:
```
0:00.5 SPEED 32.5
0:01.0 FOLLOW_DISTANCE 1.8
0:02.5 LANE_CHANGE LEFT
0:03.0 STOP_SIGN_DETECTED
```

## Violation Types
- **SPEEDING**: Vehicle speed exceeds the maximum allowed speed
- **TAILGATING**: Following distance is less than the minimum required
- **ROLLING_STOP**: Vehicle didn't stop for the required duration at a stop sign
- **UNSAFE_LANE_CHANGE**: Lane change performed while following too closely

## Testing
Run the test suite with pytest:
```bash
pytest tests_student/ -v
```

## Database Schema
The SQLite database stores the following information:
- Rulesets (road rules)
- Scenarios (test cases)
- Speed zones (geofenced speed limits)
- Violations (detected safety issues)

See `schema.sql` for the complete database schema.

## License
This project is part of an academic assignment and is not licensed for commercial use.
