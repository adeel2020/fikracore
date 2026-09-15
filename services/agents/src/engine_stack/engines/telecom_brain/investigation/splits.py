"""Deterministic stratified splitting for Step 4.1 calibration.

Partitions 100 scenario runs into:
- Calibration (60 runs): 12 per difficulty level (9 known RCA, 3 unknown RCA)
- Validation (20 runs): 4 per difficulty level (3 known RCA, 1 unknown RCA)
- Holdout (20 runs): 4 per difficulty level (3 known RCA, 1 unknown RCA)
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any
import yaml


def generate_stratified_splits(runs_dir: Path) -> Dict[str, List[str]]:
    """Partition runs deterministically into calibration (60), validation (20), and holdout (20)."""
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("RUN-")])
    
    # Group by (difficulty, is_unknown)
    groups = defaultdict(list)
    for r in runs:
        manifest_file = r / "scenario_manifest.yaml"
        exp_file = r / "hidden" / "evaluator_expectations.yaml"
        if not manifest_file.exists() or not exp_file.exists():
            continue
            
        with open(manifest_file, "r") as f:
            manifest = yaml.safe_load(f)
        with open(exp_file, "r") as f:
            expectations = yaml.safe_load(f)
            
        diff = manifest.get("difficulty_profile", {}).get("level", "L1")
        is_unknown = expectations.get("expected_terminal_state") != "EXPLAINED"
        groups[(diff, is_unknown)].append(r.name)
        
    calibration = []
    validation = []
    holdout = []
    
    # Sort groups deterministically
    for (diff, is_unknown), run_ids in sorted(groups.items()):
        run_ids = sorted(run_ids)
        n = len(run_ids)
        # For 15 known items: 9 calib, 3 val, 3 holdout
        # For 5 unknown items: 3 calib, 1 val, 1 holdout
        n_cal = round(n * 0.6)
        n_val = round(n * 0.2)
        
        cal = run_ids[:n_cal]
        val = run_ids[n_cal:n_cal + n_val]
        hold = run_ids[n_cal + n_val:]
        
        calibration.extend(cal)
        validation.extend(val)
        holdout.extend(hold)
        
    return {
        "calibration": sorted(calibration),
        "validation": sorted(validation),
        "holdout": sorted(holdout),
    }


def save_splits(runs_dir: Path, output_path: Path) -> Dict[str, List[str]]:
    """Generate and save splits JSON to output_path."""
    splits = generate_stratified_splits(runs_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(splits, f, indent=2)
    return splits


def load_splits(splits_path: Path) -> Dict[str, List[str]]:
    """Load splits JSON."""
    with open(splits_path, "r") as f:
        return json.load(f)
