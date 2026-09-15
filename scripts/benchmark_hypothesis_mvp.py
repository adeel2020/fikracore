#!/usr/bin/env python3
"""Small examiner harness using SCN-001 operational evidence, not hidden-world ingestion."""

import argparse
import json
from datetime import timedelta
from pathlib import Path

from engine_stack.engines.telecom_brain.investigation import Investigator
from engine_stack.engines.telecom_brain.investigation.evidence import input_from_run, load_evidence
from engine_stack.engines.telecom_brain.investigation.evaluator import compare
from engine_stack.engines.telecom_brain.investigation.knowledge import InMemoryKnowledgeProvider

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "services/agents/src/engine_stack/engines/telecom_brain/simulator/runs/RUN-SCN-001-L1-SEED-42001"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/hypothesis/benchmark")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    run = input_from_run(RUN)
    evidence, hashes = load_evidence(run, RUN / "operational")
    # Explicit, independently authored operational TEST knowledge for this catalog family.
    # These relationships are never uploaded to telecombrain or extracted from hidden files.
    chain = ["IP:PE:RTR-21", "IP:VRF:N3-01", "SA5G:UPF:003", "CRM:TICKET:001"]
    pages = [{"slug": entity} for entity in chain] + [{"slug": "test/unrelated-pod"}]
    relationships = [{"relationship_id": f"TEST-R{i}", "source": consumer, "target": supplier,
                      "link_type": "depends-on", "state": "CONFIRMED", "confidence": .95,
                      "provenance": "independently authored operational test fixture"}
                     for i, (supplier, consumer) in enumerate(zip(chain, chain[1:]), 1)]
    local = [e for e in evidence if e.canonical_entity == chain[0] and e.evidence_type in {"alarms", "logs", "metrics"}]
    noise = local[0].model_copy(update={"evidence_id": "TEST-NOISE", "entity": "test/unrelated-pod",
        "canonical_entity": "test/unrelated-pod", "source_native_entity": "test/unrelated-pod",
        "service": ["unrelated-service"], "event_time": local[0].event_time - timedelta(minutes=5)})
    change = noise.model_copy(update={"evidence_id": "TEST-CHANGE", "evidence_type": "changes", "polarity": "context"})
    duplicates = [evidence[1].model_copy(update={"evidence_id": f"TEST-DUP-{i}"}) for i in range(60)]
    cases = [
        ("S1", "L1", local, relationships),
        ("S2", "L1", evidence, relationships),
        ("S3", "L2", list(reversed(evidence + duplicates + [noise, change])), relationships),
        ("S4", "L4", evidence, relationships[1:]),
        ("S5", "L5", local[:1], relationships),
    ]
    results = []
    for name, level, observations, links in cases:
        case_input = run.model_copy(update={"run_id": f"MVP-{name}-SCN-001", "difficulty_profile": level})
        provider = InMemoryKnowledgeProvider(pages, links, version=f"SCN-001-operational-test-{name}-v1")
        result = Investigator(provider).investigate(case_input, observations, hashes)
        (args.output / f"{name}-investigation.json").write_text(result.model_dump_json(indent=2) + "\n")
        # Examiner labels stay here, outside the operational engine and its input contract.
        report = compare(result, [chain[0]], unknown_correct=name in {"S4", "S5"})
        report["case"] = name
        results.append(report)
    output = {"scope": "Five deterministic variations of catalog SCN-001; not the full 100-scenario benchmark",
              "cases": results,
              "baseline_correct": sum(row["baseline_correct"] for row in results),
              "method_b_correct": sum(row["method_b_correct"] for row in results),
              "caveat": "Small authored test set; no statistical or production accuracy claim."}
    (args.output / "comparison.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
