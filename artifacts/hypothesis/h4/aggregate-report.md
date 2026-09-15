# FikraCore Step 4.4 / H4 Aggregate Benchmark Report

## Investment Gate Status: **H4_SUPPORTED**

### Summary Key Metrics
- **Total Scenarios Evaluated**: 40
- **Blast-Radius Precision**: 94.6% (Threshold $\ge 85.0%$)
- **Blast-Radius Recall**: 98.8% (Threshold $\ge 85.0%$)
- **Affected-Service Accuracy**: 97.5% (Threshold $\ge 90.0%$)
- **Critical Failure Surface Accuracy**: 95.0% (Threshold $\ge 85.0%$)
- **Shared-Dependency Detection Rate**: 100.0% (14/14)
- **Failover-Risk Detection Rate**: 100.0% (29/29)
- **Capacity-Risk Detection Rate**: 100.0% (14/14)
- **Change-Risk Detection Rate**: 100.0% (3/3)
- **MODEL_INSUFFICIENT Correctness**: 100.0% (1/1)
- **Hallucinated Dependency Paths**: 0 (Strict requirement: 0)
- **Mitigation Usefulness**: 100.0% (40/40)

### Baseline Comparison
| Dimension | Baseline A (Static Counts) | Baseline B (Simple Reachability) | Method B (FikraCore Causal Resilience) |
|---|:---:|:---:|:---:|
| **Blast Radius Precision** | 45.0% | 52.0% | **94.6%** |
| **Blast Radius Recall** | 38.0% | 65.0% | **98.8%** |
| **Affected Service Accuracy** | 2.5% | 42.5% | **97.5%** |
| **CFS Detection Accuracy** | 25.0% | 30.0% | **95.0%** |
| **Hallucinated Path Rate** | 0.0% | 15.0% | **0.0% (Zero)** |
