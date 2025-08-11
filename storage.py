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
    zones: List[Dict[str, Any]] | None,
) -> int:
    """
    Insert a scenario and its optional speed zones; return the new scenario_id.

    Tables:
      - scenario(name, description, source_file, ruleset_id)
      - speed_zone(start_mile, end_mile, speed_limit, scenario_id)

    TODO(student):
      1) INSERT into scenario(...); capture lastrowid as sid.
      2) If `zones` is provided, INSERT each zone row bound to sid.
      3) Commit and return sid.
    """
    raise NotImplementedError("TODO: implement register_scenario()")


def save_report(scenario_id: int, violations: List[Dict[str, Any]]) -> None:
    """
    Persist violations for a given scenario.

    Table:
      - violation(scenario_id, tstamp, type, details)

    Input violation dicts are expected to have keys: 'time', 'type', 'details'.

    TODO(student):
      1) INSERT each violation row using parameterized queries.
      2) Commit once at the end.
    """
    raise NotImplementedError("TODO: implement save_report()")


def get_violation_counts(scenario_id: int) -> Dict[str, int]:
    """
    Return {type: count} for a scenario.

    SQL:
      SELECT type, COUNT(*)
      FROM violation
      WHERE scenario_id=?
      GROUP BY type

    TODO(student):
      1) Run the SELECT above.
      2) Build and return a dict from fetched rows.
    """
    raise NotImplementedError("TODO: implement get_violation_counts()")


def get_violations_by_type(scenario_id: int, vtype: str) -> List[Dict[str, Any]]:
    """
    Return violations of a given type for a scenario, ordered by timestamp.

    SQL:
      SELECT tstamp, type, details
      FROM violation
      WHERE scenario_id=? AND type=?
      ORDER BY tstamp

    Output shape per row:
      {"time": <str>, "type": <str>, "details": <str>}

    TODO(student):
      1) Execute the SELECT and fetch all.
      2) Convert rows to dicts with keys 'time', 'type', 'details'.
    """
    raise NotImplementedError("TODO: implement get_violations_by_type()")


def get_recent_violations(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Return the most recent `limit` violations across all scenarios (newest first).

    SQL:
      SELECT scenario_id, tstamp, type, details
      FROM violation
      ORDER BY violation_id DESC
      LIMIT ?

    Output shape per row:
      {"scenario_id": <int>, "time": <str>, "type": <str>, "details": <str>}

    TODO(student):
      1) Execute the SELECT with LIMIT ?.
      2) Convert rows to dicts with keys shown above.
    """
    raise NotImplementedError("TODO: implement get_recent_violations()")
