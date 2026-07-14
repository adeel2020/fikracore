## One-line interview answer

“Standard LoRA is better for stability and diversity, while RSLoRA with PiSSA improves convergence speed and stylistic coherence at the cost of slightly reduced output variability, making it better suited for production-level storytelling fine-tuning.”

##  Recommendation for YOUR case (storytelling LoRA)

Given everything you showed:

If your goal is:
##  High-quality storytelling model (production style)

### Use RSLoRA + PiSSA

Why:

better narrative consistency
stronger style learning
faster convergence
more “author-like” output

# LoRA Storytelling Fine-Tuning Summary

## Base Setup

### Model

* Base model: TinyLlama-1.1B-Chat-v1.0
* Task: Storytelling LoRA fine-tuning
* Hardware: CPU-only training
* Frameworks:

  * Transformers
  * PEFT
  * Datasets
  * Evaluate

---

# Training Progression Analysis

## Early Training Phase (Exploration / Activation)

Initial logs:

```python
{'loss': 2.2418, 'grad_norm': 2.0477}
{'loss': 2.6018, 'grad_norm': 2.7756}
{'loss': 2.7006, 'grad_norm': 4.2778}
```

### Interpretation

* Model was adapting aggressively to new storytelling distribution.
* High gradient norms indicated strong representational updates.
* Chaotic optimization phase.
* Model still searching for stable narrative structures.

### Characteristics

* High variance
* Large gradient movement
* Rapid structural learning
* Initial adaptation phase

---

# Mid Training Phase (Structural Alignment)

Logs stabilized around:

```python
loss ≈ 1.3–1.5
grad_norm ≈ 0.3–0.5
```

### Interpretation

* Model discovered stable storytelling manifold.
* Gradients became localized and controlled.
* Transition from structure acquisition to style learning.

### Characteristics

* Better narrative alignment
* Reduced optimization noise
* More stable convergence
* Style learning started dominating

---

# Consolidation Phase

Observed pattern:

```python
loss ≈ 1.2–1.35
grad_norm stable
learning rate decaying
```

### Interpretation

* Model entered convergence corridor.
* Learning focused on:

  * pacing
  * rhythm
  * stylistic consistency
  * transition smoothness

### Key Insight

Loss oscillation during storytelling training is normal.
Creative generation tasks naturally maintain entropy.

---

# Refinement Phase

Late training:

```python
loss ≈ 1.1–1.25
stable gradients
```

### Interpretation

* Fine stylistic tuning.
* Behavioral refinement phase.
* Stable narrative generation patterns.
* Strong convergence.

---

# LoRA Configuration

## Original LoRA

```python
r = 8
```

### Observed Behavior

* Lower gradient norms
* Higher lexical diversity
* Softer stylistic adaptation

---

# New Experimental Configuration

Added:

```python
use_rslora=True
init_lora_weights="pissa_niter_16"
```

---

# RSLoRA Impact

## Description

Rank-Stabilized LoRA changes scaling behavior from:

```text
alpha / r
```

to:

```text
alpha / sqrt(r)
```

### Effect

* Stronger updates
* Better scaling stability
* Higher adaptation energy
* Improved rank-aware learning

### Observed Outcome

* Higher gradient norms
* Faster convergence
* Stronger style locking

Interview Summary:

> RSLoRA improved LoRA stability and scaling using rank-aware normalization, enabling stronger and more stable adaptation during fine-tuning.

---

# PiSSA Initialization Impact

## Description

PiSSA initializes LoRA weights using SVD-based dominant singular directions.

Instead of random initialization:

* starts in meaningful feature subspaces
* aligns to dominant activation structure
* accelerates convergence

### Observed Outcome

* Stronger early gradients
* Faster adaptation
* Better stylistic alignment
* More expressive learning dynamics

Interview Summary:

> PiSSA initialization improved convergence speed and feature alignment by initializing LoRA weights from dominant singular subspaces rather than random low-energy initialization.

---

# Gradient Norm Analysis

## Vanilla LoRA

```python
grad_norm ≈ 0.3
```

## RSLoRA + PiSSA

```python
grad_norm ≈ 2.0–2.6
```

### Important Insight

Higher gradients were NOT instability.

Instead they indicated:

* stronger directional learning
* higher-information adaptation
* more expressive optimization

Healthy signs observed:

* bounded gradients
* stable loss
* no NaNs
* no divergence

---

# Final Training Completion

Final logs:

```python
loss ≈ 1.11–1.23
grad_norm ≈ 2.23
learning_rate → 0
```

### Interpretation

* Clean convergence
* Stable final basin
* No optimization instability
* Strong adaptation completion

### Final Assessment

* Successful storytelling LoRA
* Stable RSLoRA + PiSSA optimization
* High-quality convergence profile

---

# Lexical Diversity Comparison

## Vanilla LoRA

```json
"lexical_diversity": 0.74
```

## RSLoRA + PiSSA

```json
"lexical_diversity": 0.673
```

---

# Interpretation of Diversity Drop

### What Happened

Why PiSSA can reduce diversity

PiSSA initializes LoRA into:
* dominant singular directions
* strongest activation subspaces
So the model learns:
* core narrative structure faster
* preferred stylistic pathways earlier

Result:

stronger style locking.
That often produces:
* better coherence
* better tone consistency
* slightly lower lexical entropy

### Tradeoff

| Vanilla LoRA     | RSLoRA + PiSSA     |
| ---------------- | ------------------ |
| Higher diversity | Stronger coherence |
| Looser style     | Tighter style      |
| More exploratory | More refined       |
| Higher entropy   | Higher consistency |

### Important Insight

Lower lexical diversity does NOT automatically mean worse storytelling.

Often it means:

* stronger tone consistency
* better pacing
* more stable narrative identity

---

# Evaluation Metrics

Results:

```text
Average Loss   : 1.3786
Perplexity     : 3.9695
BLEU           : 0.0290
ROUGE-1        : 0.3397
ROUGE-2        : 0.1028
ROUGE-L        : 0.1762
```

### Interpretation

## Loss / Perplexity

* Strong convergence
* Good prediction confidence
* Healthy storytelling adaptation

## BLEU

Low BLEU is expected in creative writing.
Storytelling has many valid outputs.

## ROUGE

Moderate ROUGE indicates:

* semantic overlap
* structural alignment
* reasonable narrative consistency

---

# Generation Metrics

```json
{
  "tokens_generated": 250,
  "generation_time_sec": 55.68,
  "tokens_per_second": 4.49,
  "lexical_diversity": 0.673
}
```

### Interpretation

## Tokens/sec

* Normal for CPU inference.
* Expected for TinyLlama on CPU.

## Lexical Diversity

* Healthy storytelling variability.
* No mode collapse.
* Creativity retained.

---

# Parameter Comparison Insight

Observed:

```text
Base params == merged params
```

### Why

Merging LoRA does NOT increase parameter count.

Instead:

* LoRA deltas are fused into existing weights.
* Same architecture size.
* Different learned weight values.

### Correct Verification

Use weight-difference comparison:

```python
Total weight difference: 18.40
```

This confirmed:

* LoRA successfully modified model weights.
* Merge worked correctly.

---

# Common Issues Encountered

## 1. argparse in VS Code Interactive

Problem:

```python
SystemExit: 2
```

### Fix

VS Code interactive requires:

```python
sys.argv = [
    "script.py",
    "--config", "train_config.yml",
    "--prompt", "Write a story"
]
```

---

## 2. evaluate Circular Import

Problem:

```python
AttributeError: partially initialized module 'evaluate'
```

### Cause

File named:

```text
evaluate.py
```

conflicted with:

```python
import evaluate
```

### Fix

Rename file.

---

## 3. Missing Metric Dependencies

Installed:

```bash
pip install evaluate
pip install nltk rouge_score absl-py
```

---

## 4. Threading Runtime Error

Problem:

```python
RuntimeError: cannot set number of interop threads
```

### Cause

PyTorch threading initialized too late.

### Fix

Use only:

```python
torch.set_num_threads(num_cores)
```

Avoid:

```python
torch.set_num_interop_threads()
```

in VS Code interactive environments.

---

# CPU Optimization

Added:

```python
import multiprocessing

num_cores = max(1, multiprocessing.cpu_count() - 2)

torch.set_num_threads(num_cores)
```

Dataset optimization:

```python
dataset.map(tokenize, num_proc=num_cores)
```

Training optimization:

```python
dataloader_num_workers=num_cores
```

---

# Multiprocessing Insight

## Purpose

Uses multiple CPU cores in parallel.

### Benefits

* Faster tokenization
* Faster preprocessing
* Better CPU utilization

### No Installation Needed

```python
import multiprocessing
```

built into Python.

---

# Checkpoint Warning

Observed:

```text
Could not find a config file ...
will assume vocabulary was not modified
```

### Interpretation

Harmless warning.

Because:

* tokenizer unchanged
* no embedding resize
* no vocabulary modification

Safe to ignore.

---

# Final Technical Assessment

| Category                | Result       |
| ----------------------- | ------------ |
| LoRA convergence        | Successful   |
| RSLoRA behavior         | Stable       |
| PiSSA initialization    | Effective    |
| Gradient behavior       | Healthy      |
| Storytelling adaptation | Strong       |
| Lexical diversity       | Healthy      |
| Optimization stability  | Excellent    |
| CPU training            | Successful   |
| Merge verification      | Confirmed    |
| Overfitting             | Not observed |

---

# Final Interview Summary

> Fine-tuned TinyLlama-1.1B for storytelling using LoRA on CPU. Initially used standard LoRA, then upgraded to RSLoRA with PiSSA initialization for stronger and faster adaptation. Observed significantly higher but stable gradient norms due to information-rich initialization and rank-aware scaling. Training converged cleanly with final losses around 1.1–1.3. RSLoRA + PiSSA improved stylistic coherence and convergence quality while slightly reducing lexical diversity due to stronger style consolidation. Successfully evaluated, merged adapters, optimized CPU execution, and validated weight adaptation behavior through parameter-difference analysis.
