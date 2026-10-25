"""Compatibility entry point for the generic, validated benchmark analyzer.

Use experiments/analyze_synthetic_results.py directly for new work. This legacy
filename intentionally delegates rather than maintaining a second stale analyzer
with a hard-coded historical result path.
"""
import runpy
import sys
from pathlib import Path

script = Path(__file__).with_name("analyze_synthetic_results.py")
sys.argv[0] = str(script)
runpy.run_path(str(script), run_name="__main__")
