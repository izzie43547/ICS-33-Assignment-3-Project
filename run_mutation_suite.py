#!/usr/bin/env python3
"""
Run mutation testing on the rules.py file and generate a mutation_results.json file.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configuration
RULES_FILE = "rules.py"
MUTANTS_DIR = "mutants"
TEST_DIR = "tests_student"
RESULTS_FILE = "mutation_results.json"


def run_tests() -> Tuple[bool, str]:
    """Run the test suite and return success status and output."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", TEST_DIR, "-v"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0, result.stdout + "\n" + result.stderr
    except Exception as e:
        return False, str(e)


def create_mutant(original_file: str, line_num: int, original: str, mutant: str) -> str:
    """Create a mutant by modifying the original file."""
    with open(original_file, 'r') as f:
        lines = f.readlines()
    
    if line_num < 1 or line_num > len(lines):
        raise ValueError(f"Line number {line_num} out of range (1-{len(lines)})")
    
    line_idx = line_num - 1
    if original not in lines[line_idx]:
        raise ValueError(f"Original text '{original}' not found in line {line_num}")
    
    lines[line_idx] = lines[line_idx].replace(original, mutant, 1)
    
    mutant_file = os.path.join(MUTANTS_DIR, f"mutant_{line_num}_{hash(original)}.py")
    with open(mutant_file, 'w') as f:
        f.writelines(lines)
    
    return mutant_file


def run_mutation_test(original_file: str, mutant_file: str) -> Dict:
    """Run tests on a mutant and return the results."""
    # Backup original
    backup_file = original_file + ".bak"
    shutil.copy2(original_file, backup_file)
    
    try:
        # Replace with mutant
        shutil.copy2(mutant_file, original_file)
        
        # Run tests
        passed, output = run_tests()
        
        return {
            "mutant_file": mutant_file,
            "killed": not passed,
            "output": output,
        }
    finally:
        # Restore original
        shutil.copy2(backup_file, original_file)
        os.remove(backup_file)


def main():
    """Main function to run the mutation test suite."""
    # Create mutants directory if it doesn't exist
    os.makedirs(MUTANTS_DIR, exist_ok=True)
    
    # Define mutations for rules.py
    mutations = [
        # Mutation 1: Change the comparison operator for speed check
        {
            "line": 93,
            "original": "                if speed > current_max_speed + 1e-9:  # Add small epsilon for floating point comparison",
            "mutant": "                if speed > current_max_speed + 1.0:  # Changed threshold to make it harder to detect",
            "description": "Changed speed comparison threshold"
        },
        # Mutation 2: Change the rolling stop speed threshold
        {
            "line": 102,
            "original": "                if stop_sign_time is not None and speed > 1.0 + 1e-9:",
            "mutant": "                if stop_sign_time is not None and speed > 5.0 + 1e-9:  # Increased threshold",
            "description": "Increased rolling stop speed threshold"
        },
        # Mutation 3: Change the follow distance comparison
        {
            "line": 120,
            "original": "                if dist < min_follow - 1e-9:  # Add small epsilon for floating point comparison",
            "mutant": "                if dist < min_follow + 1.0:  # Changed threshold",
            "description": "Changed follow distance comparison"
        },
        # Mutation 4: Change the stop sign wait time check
        {
            "line": 103,
            "original": "                    if time_since_stop < stop_wait - 1e-9:  # Add small epsilon for floating point comparison",
            "mutant": "                    if time_since_stop < stop_wait + 5.0:  # Increased threshold",
            "description": "Increased stop sign wait time threshold"
        },
        # Mutation 5: Change the unsafe lane change check
        {
            "line": 133,
            "original": "            if last_follow_dist < min_follow - 1e-9:  # Add small epsilon for floating point comparison",
            "mutant": "            if last_follow_dist < min_follow + 1.0:  # Changed threshold",
            "description": "Changed unsafe lane change threshold"
        },
        # Mutation 6: Change the speed zone check
        {
            "line": 90,
            "original": "                        current_max_speed = min(current_max_speed, float(zone['speed_limit']))",
            "mutant": "                        current_max_speed = max(current_max_speed, float(zone['speed_limit']))  # Changed from min to max",
            "description": "Changed speed zone check from min to max"
        },
        # Mutation 7: Change the stop sign detection
        {
            "line": 142,
            "original": "            stop_sign_time = time_sec",
            "mutant": "            # stop_sign_time = time_sec  # Commented out stop sign detection",
            "description": "Disabled stop sign detection"
        }
    ]
    
    results = {
        "total_mutants": 0,
        "killed_mutants": 0,
        "mutation_score": 0.0,
        "details": []
    }
    
    # Run mutation tests
    for mutation in mutations:
        try:
            mutant_file = create_mutant(
                RULES_FILE,
                mutation["line"],
                mutation["original"],
                mutation["mutant"]
            )
            
            result = run_mutation_test(RULES_FILE, mutant_file)
            result.update({
                "line": mutation["line"],
                "original": mutation["original"],
                "mutant": mutation["mutant"],
                "description": mutation["description"]
            })
            
            results["total_mutants"] += 1
            if result["killed"]:
                results["killed_mutants"] += 1
            
            results["details"].append(result)
            
        except Exception as e:
            print(f"Error running mutation test: {e}", file=sys.stderr)
    
    # Calculate mutation score
    if results["total_mutants"] > 0:
        results["mutation_score"] = results["killed_mutants"] / results["total_mutants"]
    
    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Mutation testing complete. Score: {results['mutation_score']:.1%} "
          f"({results['killed_mutants']}/{results['total_mutants']} mutants killed)")
    print(f"Results saved to {RESULTS_FILE}")
    
    return 0 if results["mutation_score"] >= 0.6 else 1


if __name__ == "__main__":
    sys.exit(main())
