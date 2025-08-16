from __future__ import annotations
from typing import Dict, List

def make_report(scenario: Dict, violations: List[Dict[str, str]]) -> Dict:
    """
    Build a report dict from a scenario and a list of violation records.

    Expected output shape:
      {
        "scenario": <str>,              # scenario name or "Unnamed" fallback
        "violations": <list[dict]>,     # as provided
        "total_violations": <int>       # len(violations)
      }

    TODO(student):
      1) Read the scenario name via scenario.get('name'); fall back to "Unnamed" if falsy.
      2) Include the provided violations list unchanged under key "violations".
      3) Compute "total_violations" as len(violations).
      4) Return the assembled dict.
    """
    raise NotImplementedError("TODO: implement make_report()")
