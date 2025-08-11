#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Import the implemented modules
import parser as parser_mod
import rules as rules_mod
import report as report_mod
import storage as storage_mod


def print_summary(violation_counts: Dict[str, int]) -> None:
    """Print a formatted summary of violation counts."""
    if not violation_counts:
        print("No violations found.")
        return
    
    max_type_len = max(len(vtype) for vtype in violation_counts)
    print("Violation Summary:")
    print("-" * (max_type_len + 10))
    for vtype, count in sorted(violation_counts.items()):
        print(f"{vtype:<{max_type_len}}: {count}")


def main(argv: list[str] | None = None) -> int:
    """
    Incident Log Analyzer

    Modes:
      1) Summary mode:       --summary N --db DB.sqlite
      2) By-type query:      --by-type SCENARIO_ID TYPE --db DB.sqlite
      3) Analyze a run:      SCENARIO.json LOGFILE.txt [--db DB.sqlite]
    """
    argv = argv if argv is not None else sys.argv[1:]

    ap = argparse.ArgumentParser(description="Incident Log Analyzer")
    ap.add_argument("scenario", nargs="?", help="Path to scenario JSON")
    ap.add_argument("logfile", nargs="?", help="Path to event log")
    ap.add_argument("--db", help="Path to SQLite database for persistence")
    ap.add_argument("--summary", type=int, 
                   help="Print violation counts for the N most recent runs")
    ap.add_argument("--by-type", nargs=2, metavar=("SCENARIO_ID", "TYPE"),
                   help="List violations of a given TYPE for a scenario ID")
    
    args = ap.parse_args(argv)

    # ----- Summary mode ------------------------------------------------------
    if args.summary is not None:
        if not args.db:
            print("Error: --summary requires --db", file=sys.stderr)
            return 2

        try:
            storage_mod.init_db(args.db)
            recent_violations = storage_mod.get_recent_violations(args.summary)
            
            if not recent_violations:
                print("No recent violations found.")
                return 0
                
            # Group violations by scenario
            scenarios: Dict[int, Dict[str, Any]] = {}
            for v in recent_violations:
                sid = v['scenario_id']
                if sid not in scenarios:
                    scenarios[sid] = {
                        'name': v['scenario_name'],
                        'violations': {}
                    }
                scenarios[sid]['violations'][v['type']] = \
                    scenarios[sid]['violations'].get(v['type'], 0) + 1
            
            # Print summary
            for sid, data in scenarios.items():
                print(f"\nScenario {sid}: {data['name']}")
                print_summary(data['violations'])
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
            
        return 0

    # ----- By-type mode ------------------------------------------------------
    if args.by_type is not None:
        if not args.db:
            print("Error: --by-type requires --db", file=sys.stderr)
            return 2

        # Inputs come in as strings; convert scenario id to int.
        sid_str, vtype = args.by_type
        try:
            scenario_id = int(sid_str)
        except ValueError:
            print("Error: SCENARIO_ID must be an integer", file=sys.stderr)
            return 2

        try:
            storage_mod.init_db(args.db)
            violations = storage_mod.get_violations_by_type(scenario_id, vtype)
            
            if not violations:
                print(f"No violations of type '{vtype}' found for scenario {scenario_id}.")
                return 0
                
            print(f"\nViolations of type '{vtype}' for scenario {scenario_id}:")
            print("-" * 80)
            for v in violations:
                print(f"Time: {v['time']}")
                print(f"Details: {v['details']}")
                print("-" * 80)
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
            
        return 0

    # ----- Analyze a scenario + log ------------------------------------------
    if not args.scenario or not args.logfile:
        ap.print_help()
        return 2

    scenario_path = Path(args.scenario)
    logfile_path = Path(args.logfile)

    # Basic file existence checks
    if not scenario_path.exists():
        print(f"Error: scenario file not found: {scenario_path}", file=sys.stderr)
        return 2
    if not logfile_path.exists():
        print(f"Error: log file not found: {logfile_path}", file=sys.stderr)
        return 2

    try:
        # 1. Load scenario and parse log
        scenario = parser_mod.load_scenario(scenario_path)
        events = list(parser_mod.read_log(logfile_path))
        
        # 2. Detect violations
        violations = rules_mod.detect_violations(scenario, events)
        
        # 3. Generate report
        report = report_mod.make_report(scenario, violations)
        
        # 4. Save report to JSON
        output_file = 'report.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        # 5. Print summary to console
        print(f"\nAnalysis complete. Report saved to {output_file}")
        print(f"Scenario: {report['scenario']}")
        print(f"Total violations: {report['total_violations']}")
        
        # Count violations by type for the summary
        violation_counts: Dict[str, int] = {}
        for v in report['violations']:
            violation_counts[v['type']] = violation_counts.get(v['type'], 0) + 1
        
        print_summary(violation_counts)
        
        # 6. Save to database if requested
        if args.db:
            storage_mod.init_db(args.db)
            
            # Upsert ruleset and get rule_id
            rule_id = storage_mod.upsert_ruleset(scenario['road_rules'])
            
            # Register scenario and get scenario_id
            scenario_id = storage_mod.register_scenario(
                name=scenario.get('name', 'Unnamed'),
                source_file=str(scenario_path),
                rule_id=rule_id,
                description=scenario.get('description', ''),
                speed_zones=scenario.get('speed_zones', [])
            )
            
            # Save violations to database
            storage_mod.save_report(scenario_id, report['violations'])
            print(f"\nResults saved to database (scenario_id: {scenario_id})")
        
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
