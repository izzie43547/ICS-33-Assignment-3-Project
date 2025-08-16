#!/usr/bin/env python3
"""
Run mutation testing on the rules.py file and generate a mutation_results.json file.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

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


def create_mutations(original_file: str) -> List[Dict[str, Any]]:
    """Generate mutations for the given file."""
    with open(original_file, 'r') as f:
        source = f.read()
    
    # Parse the source code to get line numbers for specific constructs
    tree = ast.parse(source)
    
    # Find the detect_violations function
    detect_violations = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'detect_violations':
            detect_violations = node
            break
    
    if not detect_violations:
        raise ValueError("Could not find detect_violations function in rules.py")
    
    # Get the line numbers where the function starts and ends
    start_line = detect_violations.lineno
    end_line = max(node.end_lineno for node in ast.walk(detect_violations) 
                  if hasattr(node, 'end_lineno'))
    
    # Read the relevant lines
    lines = source.splitlines()
    function_lines = lines[start_line-1:end_line]
    
    # Define mutation patterns
    patterns = [
        # Pattern 1: Change floating point comparisons with epsilon
        {
            'pattern': r'(\s*if\s+[^:]+?)\s*[<>]=?\s*([a-zA-Z_][a-zA-Z0-9_]*\s*[+-]\s*1e-9\b)',
            'replacement': r'\1 > \2 + 1.0',  # Change comparison to make it harder to trigger
            'description': 'Changed floating point comparison with epsilon'
        },
        # Pattern 2: Change min to max in speed zone check
        {
            'pattern': r'(\s*current_max_speed\s*=\s*)min\(',
            'replacement': r'\1max(',
            'description': 'Changed min to max in speed zone check'
        },
        # Pattern 3: Comment out stop sign detection
        {
            'pattern': r'(\s*)(stop_sign_time\s*=\s*time_sec\b)',
            'replacement': r'\1# \2  # Mutation: Commented out stop sign detection',
            'description': 'Commented out stop sign detection'
        },
        # Pattern 4: Change speed threshold for rolling stop
        {
            'pattern': r'(\s*if\s+stop_sign_time\s+is\s+not\s+None\s+and\s+speed\s*>\s*)(1\.0\s*\+\s*1e-9\b)',
            'replacement': r'\g<1>5.0 + 1e-9',
            'description': 'Increased speed threshold for rolling stop detection'
        },
        # Pattern 5: Change stop sign wait time check
        {
            'pattern': r'(\s*if\s+time_since_stop\s*<\s*)(stop_wait\s*-\s*1e-9\b)',
            'replacement': r'\1(\2 + 5.0)',
            'description': 'Increased stop sign wait time threshold'
        }
    ]
    
    mutations = []
    
    # Apply patterns to find potential mutations
    for i, line in enumerate(function_lines, start=start_line):
        for pattern in patterns:
            if re.search(pattern['pattern'], line):
                mutant_line = re.sub(pattern['pattern'], pattern['replacement'], line)
                if mutant_line != line:  # Only add if the line actually changes
                    mutations.append({
                        'line': i,
                        'original': line,
                        'mutant': mutant_line,
                        'description': pattern['description']
                    })
    
    return mutations


def create_mutant(original_file: str, line_num: int, original: str, mutant: str) -> str:
    """Create a mutant by modifying the original file."""
    with open(original_file, 'r') as f:
        lines = f.readlines()
    
    line_idx = line_num - 1
    if line_idx < 0 or line_idx >= len(lines):
        raise ValueError(f"Line number {line_num} out of range (1-{len(lines)})")
    
    # Create a copy of the lines
    mutant_lines = lines.copy()
    mutant_lines[line_idx] = mutant + '\n' if not mutant.endswith('\n') else mutant
    
    # Create a unique name for the mutant file
    mutant_name = f"mutant_{line_num}_{abs(hash(original + mutant))}.py"
    mutant_file = os.path.join(MUTANTS_DIR, mutant_name)
    
    # Write the mutant file
    with open(mutant_file, 'w') as f:
        f.writelines(mutant_lines)
    
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
            'killed': not passed,
            'output': output,
        }
    finally:
        # Restore original
        shutil.copy2(backup_file, original_file)
        os.remove(backup_file)


def main():
    """Main function to run the mutation test suite."""
    # Create mutants directory if it doesn't exist
    os.makedirs(MUTANTS_DIR, exist_ok=True)
    
    # Generate mutations based on the actual file content
    try:
        mutations = create_mutations(RULES_FILE)
    except Exception as e:
        print(f"Error generating mutations: {e}", file=sys.stderr)
        return 1
    
    if not mutations:
        print("No mutations generated. Check if the source file has the expected patterns.", file=sys.stderr)
        return 1
    
    print(f"Generated {len(mutations)} mutations to test.")
    
    results = {
        'total_mutants': 0,
        'killed_mutants': 0,
        'mutation_score': 0.0,
        'details': []
    }
    
    # Run mutation tests
    for i, mutation in enumerate(mutations, 1):
        print(f"Testing mutation {i}/{len(mutations)}: {mutation['description']} (line {mutation['line']})")
        
        try:
            # Create mutant file
            mutant_file = create_mutant(
                RULES_FILE,
                mutation['line'],
                mutation['original'],
                mutation['mutant']
            )
            
            # Run tests on the mutant
            test_result = run_mutation_test(RULES_FILE, mutant_file)
            
            # Record results
            result = {
                'line': mutation['line'],
                'original': mutation['original'].strip(),
                'mutant': mutation['mutant'].strip(),
                'description': mutation['description'],
                'killed': test_result['killed'],
                'test_output': test_result['output']
            }
            
            results['total_mutants'] += 1
            if result['killed']:
                results['killed_mutants'] += 1
            
            results['details'].append(result)
            
            print(f"  - {'KILLED' if result['killed'] else 'SURVIVED'}: {mutation['description']}")
            
        except Exception as e:
            print(f"  - ERROR: {e}", file=sys.stderr)
            results['details'].append({
                'line': mutation.get('line', 0),
                'error': str(e),
                'description': mutation.get('description', 'Unknown')
            })
    
    # Calculate mutation score
    if results['total_mutants'] > 0:
        results['mutation_score'] = results['killed_mutants'] / results['total_mutants']
    
    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nMutation testing complete. Score: {results['mutation_score']:.1%} "
          f"({results['killed_mutants']}/{results['total_mutants']} mutants killed)")
    print(f"Results saved to {RESULTS_FILE}")
    
    # Return non-zero exit code if mutation score is below threshold
    return 0 if results['mutation_score'] >= 0.6 else 1


if __name__ == "__main__":
    sys.exit(main())
