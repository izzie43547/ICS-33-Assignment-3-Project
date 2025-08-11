from __future__ import annotations
from typing import Dict, List, Any

def make_report(scenario: Dict[str, Any], violations: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Build a report dict from a scenario and a list of violation records.

    Args:
        scenario: Dictionary containing scenario information, including 'name'
        violations: List of violation dictionaries, each with 'type', 'time', and 'details'
        
    Returns:
        A dictionary with the following structure:
        {
            "scenario": str,               # Scenario name or "Unnamed" if not provided
            "violations": List[Dict],      # The input violations list
            "total_violations": int        # Number of violations
        }
        
    Example:
        >>> scenario = {"name": "Test Scenario"}
        >>> violations = [{"type": "SPEEDING", "time": "00:01.0", "details": "45 mph in 35 mph zone"}]
        >>> make_report(scenario, violations)
        {
            'scenario': 'Test Scenario',
            'violations': [{'type': 'SPEEDING', 'time': '00:01.0', 'details': '45 mph in 35 mph zone'}],
            'total_violations': 1
        }
    """
    return {
        "scenario": scenario.get('name', 'Unnamed'),
        "violations": violations,
        "total_violations": len(violations)
    }
