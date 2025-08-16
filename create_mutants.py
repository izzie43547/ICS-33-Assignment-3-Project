#!/usr/bin/env python3
"""
Helper script to create mutant files for mutation testing.
"""
import os
import shutil
from pathlib import Path

# Paths
ROOT = Path(__file__).parent
RULES_FILE = ROOT / "rules.py"
MUTANTS_DIR = ROOT / "mutants"

# Create mutants directory if it doesn't exist
MUTANTS_DIR.mkdir(exist_ok=True)

# Read the original rules.py content
with open(RULES_FILE, 'r', encoding='utf-8') as f:
    original_content = f.read()

def create_mutant(mutant_name: str, original: str, replacement: str) -> None:
    """Create a mutant file with the given replacement."""
    mutant_content = original_content.replace(original, replacement, 1)
    mutant_file = MUTANTS_DIR / f"rules_{mutant_name}.py"
    with open(mutant_file, 'w', encoding='utf-8') as f:
        f.write(mutant_content)
    print(f"Created mutant: {mutant_file}")

# Mutation 1: Change speed comparison operator
try:
    original = 'if speed > current_max_speed + 1e-9:  # Add small epsilon for floating point comparison'
    replacement = 'if speed >= current_max_speed:  # Mutant: Changed > to >='
    create_mutant("speed_ge", original, replacement)
except Exception as e:
    print(f"Error creating speed_ge mutant: {e}")

# Mutation 2: Change follow distance comparison
try:
    original = 'if dist < min_follow - 1e-9:  # Add small epsilon for floating point comparison'
    replacement = 'if dist <= min_follow:  # Mutant: Changed < to <='
    create_mutant("dist_le", original, replacement)
except Exception as e:
    print(f"Error creating dist_le mutant: {e}")

# Mutation 3: Change rolling stop speed threshold
try:
    original = 'if stop_sign_time is not None and speed > 1.0 + 1e-9:'
    replacement = 'if stop_sign_time is not None and speed > 2.0:  # Mutant: Changed 1.0 to 2.0'
    create_mutant("stop_speed_2", original, replacement)
except Exception as e:
    print(f"Error creating stop_speed_2 mutant: {e}")

# Mutation 4: Change stop sign wait time check
try:
    original = 'if time_since_stop < stop_wait - 1e-9:  # Add small epsilon for floating point comparison'
    replacement = 'if time_since_stop < stop_wait + 1.0:  # Mutant: Added 1.0 to stop_wait'
    create_mutant("stop_wait_plus_1", original, replacement)
except Exception as e:
    print(f"Error creating stop_wait_plus_1 mutant: {e}")

# Mutation 5: Change lane change follow distance check
try:
    original = 'if last_follow_dist < min_follow - 1e-9:  # Add small epsilon for floating point comparison'
    replacement = 'if last_follow_dist < min_follow + 1.0:  # Mutant: Added 1.0 to min_follow'
    create_mutant("lane_change_dist_plus_1", original, replacement)
except Exception as e:
    print(f"Error creating lane_change_dist_plus_1 mutant: {e}")

# Mutation 6: Change speed zone check
try:
    original = 'current_max_speed = min(current_max_speed, float(zone[\'speed_limit\']))'
    replacement = 'current_max_speed = max(current_max_speed, float(zone[\'speed_limit\']))  # Mutant: Changed min to max'
    create_mutant("speed_zone_max", original, replacement)
except Exception as e:
    print(f"Error creating speed_zone_max mutant: {e}")

# Mutation 7: Change stop sign detection
try:
    original = 'stop_sign_time = time_sec'
    replacement = 'stop_sign_time = None  # Mutant: Disabled stop sign detection'
    create_mutant("no_stop_sign", original, replacement)
except Exception as e:
    print(f"Error creating no_stop_sign mutant: {e}")

# Mutation 8: Change sorting order
# This one should be killed by tests that check violation ordering
try:
    original = 'violations.sort(key=lambda v: v[\'time\'])'
    replacement = 'violations.sort(key=lambda v: v[\'time\'], reverse=True)  # Mutant: Reversed sort order'
    create_mutant("reverse_sort", original, replacement)
except Exception as e:
    print(f"Error creating reverse_sort mutant: {e}")

print("\nMutation files created in the 'mutants' directory.")
print("Run the mutation tests with: python run_mutation_suite.py")
