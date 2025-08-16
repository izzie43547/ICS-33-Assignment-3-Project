from __future__ import annotations
import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

_DB: Optional[sqlite3.Connection] = None


def _conn() -> sqlite3.Connection:
    """Internal: return the initialized DB connection."""
    assert _DB is not None, "DB not initialized"
    return _DB


def init_db(path: str) -> None:
    """
    Open (or create) the SQLite DB at `path`, enable foreign keys, and apply schema.sql.

    Args:
        path: Path to the SQLite database file
        
    Raises:
        sqlite3.Error: If there's an error initializing the database
        FileNotFoundError: If schema.sql is not found
    """
    global _DB
    
    # Create directory if it doesn't exist
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to the database
    _DB = sqlite3.connect(db_path)
    _DB.row_factory = sqlite3.Row  # Enable dictionary-style access to rows
    
    # Enable foreign key constraints
    _DB.execute('PRAGMA foreign_keys = ON;')
    
    # Read and execute schema.sql
    schema_path = Path(__file__).parent / 'schema.sql'
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    _DB.executescript(schema_sql)
    _DB.commit()


def upsert_ruleset(rules: Dict[str, Any]) -> int:
    """
    Return the existing ruleset.rule_id if a row with identical values exists,
    otherwise insert a new row and return its rule_id.

    Args:
        rules: Dictionary containing road rules with keys:
               - 'max_speed': Maximum allowed speed (float)
               - 'min_follow_distance': Minimum following distance (float)
               - 'stop_sign_wait': Required stop time at stop signs (float)
               
    Returns:
        int: The rule_id of the existing or newly created ruleset
        
    Raises:
        ValueError: If required keys are missing from the rules dictionary
        sqlite3.Error: If there's a database error
    """
    required_keys = {'max_speed', 'min_follow_distance', 'stop_sign_wait'}
    missing_keys = required_keys - rules.keys()
    if missing_keys:
        raise ValueError(f"Missing required rule keys: {', '.join(missing_keys)}")
    
    # Extract values with type conversion
    try:
        max_speed = float(rules['max_speed'])
        min_follow = float(rules['min_follow_distance'])
        stop_wait = float(rules['stop_sign_wait'])
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid rule value: {e}")
    
    conn = _conn()
    
    # Check if an identical ruleset exists
    cursor = conn.execute(
        """
        SELECT rule_id FROM ruleset 
        WHERE abs(max_speed - ?) < 1e-9 
          AND abs(min_follow_distance - ?) < 1e-9 
          AND abs(stop_sign_wait - ?) < 1e-9
        """,
        (max_speed, min_follow, stop_wait)
    )
    
    existing = cursor.fetchone()
    if existing:
        return existing['rule_id']
    
    # Insert new ruleset
    cursor = conn.execute(
        """
        INSERT INTO ruleset (max_speed, min_follow_distance, stop_sign_wait)
        VALUES (?, ?, ?)
        """,
        (max_speed, min_follow, stop_wait)
    )
    conn.commit()
    
    return cursor.lastrowid


def register_scenario(
    name: str,
    description: str,
    source_file: str,
    rule_id: int,
    speed_zones: Optional[List[Dict[str, float]]] = None
) -> int:
    """
    Insert a new scenario and its speed zones, returning scenario.scenario_id.

    Args:
        name: Name of the scenario
        description: Description of the scenario
        source_file: Path to the source file for this scenario
        rule_id: ID of the ruleset to associate with this scenario
        speed_zones: Optional list of speed zone dictionaries, each with:
                    - 'start_mile': Starting mile marker (float)
                    - 'end_mile': Ending mile marker (float)
                    - 'speed_limit': Speed limit in this zone (float)
                    
    Returns:
        int: The scenario_id of the newly created scenario
        
    Raises:
        sqlite3.Error: If there's a database error
    """
    if speed_zones is None:
        speed_zones = []
    
    conn = _conn()
    
    try:
        # Insert the scenario
        cursor = conn.execute(
            """
            INSERT INTO scenario (name, description, source_file, rule_id)
            VALUES (?, ?, ?, ?)
            """,
            (name, description, source_file, rule_id)
        )
        scenario_id = cursor.lastrowid
        
        # Insert speed zones if any
        if speed_zones:
            zone_data = [
                (scenario_id, zone['start_mile'], zone['end_mile'], zone['speed_limit'])
                for zone in speed_zones
            ]
            conn.executemany(
                """
                INSERT INTO speed_zone (scenario_id, start_mile, end_mile, speed_limit)
                VALUES (?, ?, ?, ?)
                """,
                zone_data
            )
        
        conn.commit()
        return scenario_id
        
    except sqlite3.Error as e:
        conn.rollback()
        raise e


def save_report(scenario_id: int, violations: List[Dict[str, Any]]) -> None:
    """
    Save a list of violations for a given scenario.

    Args:
        scenario_id: ID of the scenario these violations belong to
        violations: List of violation dictionaries, each with:
                   - 'type': Type of violation (str)
                   - 'time': Timestamp in 'MM:SS.s' format (str)
                   - 'details': Description of the violation (str)
                   
    Raises:
        ValueError: If scenario_id is invalid or violation format is incorrect
        sqlite3.Error: If there's a database error
    """
    if not violations:
        return  # Nothing to save
    
    # Validate input format
    required_keys = {'type', 'time', 'details'}
    for i, violation in enumerate(violations):
        missing_keys = required_keys - violation.keys()
        if missing_keys:
            raise ValueError(f"Violation at index {i} missing keys: {', '.join(missing_keys)}")
    
    conn = _conn()
    
    try:
        # Verify the scenario exists
        cursor = conn.execute(
            "SELECT 1 FROM scenario WHERE scenario_id = ?",
            (scenario_id,)
        )
        if not cursor.fetchone():
            raise ValueError(f"Scenario with ID {scenario_id} does not exist")
        
        # Prepare violation data
        violation_data = [
            (scenario_id, viol['time'], viol['type'], viol['details'])
            for viol in violations
        ]
        
        # Insert all violations in a single transaction
        conn.executemany(
            """
            INSERT INTO violation (scenario_id, tstamp, type, details)
            VALUES (?, ?, ?, ?)
            """,
            violation_data
        )
        
        conn.commit()
        
    except sqlite3.Error as e:
        conn.rollback()
        raise e


def get_violation_counts(scenario_id: int) -> Dict[str, int]:
    """
    Return a dictionary mapping violation types to their counts for the given scenario.

    Args:
        scenario_id: ID of the scenario to get violation counts for
        
    Returns:
        Dictionary where keys are violation types (str) and values are counts (int).
        Example: {"SPEEDING": 2, "TAILGATING": 1}
        
    Raises:
        ValueError: If scenario_id is invalid
        sqlite3.Error: If there's a database error
    """
    conn = _conn()
    
    # Verify the scenario exists
    cursor = conn.execute(
        "SELECT 1 FROM scenario WHERE scenario_id = ?",
        (scenario_id,)
    )
    if not cursor.fetchone():
        raise ValueError(f"Scenario with ID {scenario_id} does not exist")
    
    # Get violation counts by type
    cursor = conn.execute(
        """
        SELECT type, COUNT(*) as count 
        FROM violation 
        WHERE scenario_id = ? 
        GROUP BY type
        ORDER BY count DESC
        """,
        (scenario_id,)
    )
    
    # Convert to dictionary
    return {row['type']: row['count'] for row in cursor}


def get_violations_by_type(scenario_id: int, vtype: str) -> List[Dict[str, Any]]:
    """
    Return all violations of a specific type for a given scenario.

    Args:
        scenario_id: ID of the scenario to get violations for
        vtype: Type of violation to filter by (e.g., 'SPEEDING', 'TAILGATING')
        
    Returns:
        List of violation dictionaries, each with:
        - 'time': Timestamp in 'MM:SS.s' format (str)
        - 'type': Type of violation (str)
        - 'details': Description of the violation (str)
        
    Raises:
        ValueError: If scenario_id is invalid or vtype is empty
        sqlite3.Error: If there's a database error
    """
    if not vtype:
        raise ValueError("Violation type cannot be empty")
    
    conn = _conn()
    
    # Verify the scenario exists
    cursor = conn.execute(
        "SELECT 1 FROM scenario WHERE scenario_id = ?",
        (scenario_id,)
    )
    if not cursor.fetchone():
        raise ValueError(f"Scenario with ID {scenario_id} does not exist")
    
    # Get violations of the specified type
    cursor = conn.execute(
        """
        SELECT tstamp, details
        FROM violation
        WHERE scenario_id = ? AND type = ?
        ORDER BY tstamp
        """,
        (scenario_id, vtype)
    )
    
    # Convert to list of dictionaries with the required structure
    return [
        {
            'time': row['tstamp'],
            'type': vtype,
            'details': row['details']
        }
        for row in cursor
    ]


def get_recent_violations(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Return the most recent violations across all scenarios.

    Args:
        limit: Maximum number of violations to return (default: 20)
        
    Returns:
        List of violation dictionaries, each with:
        - 'scenario_id': ID of the scenario (int)
        - 'scenario_name': Name of the scenario (str)
        - 'time': Timestamp in 'MM:SS.s' format (str)
        - 'type': Type of violation (str)
        - 'details': Description of the violation (str)
        
    Raises:
        ValueError: If limit is not a positive integer
        sqlite3.Error: If there's a database error
    """
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("Limit must be a positive integer")
    
    conn = _conn()
    
    # Get recent violations with scenario information
    cursor = conn.execute(
        """
        SELECT 
            v.scenario_id, 
            s.name as scenario_name, 
            v.tstamp, 
            v.type, 
            v.details
        FROM violation v
        JOIN scenario s ON v.scenario_id = s.scenario_id
        ORDER BY v.created_at DESC, v.violation_id DESC
        LIMIT ?
        """,
        (limit,)
    )
    
    # Convert to list of dictionaries with the required structure
    return [
        {
            'scenario_id': row['scenario_id'],
            'scenario_name': row['scenario_name'],
            'time': row['tstamp'],
            'type': row['type'],
            'details': row['details']
        }
        for row in cursor
    ]
