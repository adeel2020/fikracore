# Backend Component: Context-Oriented Decomposition Adaptation (`backend/sft/`)

This component manages supervised fine-tuning configurations, data preprocessing, and the CorDA model-training pipeline.

---

## Why (The Problem It Solves)
While RAG retrieves external documents, it does not change how a language model speaks or reasons.
* In telecommunications, models must write diagnostic responses matching highly specific technical structures, log formats, and vocabulary.
* Standard LoRA (Low-Rank Adaptation) updates weights randomly, which can lead to catastrophic forgetting of base model reasoning or focus updates on non-critical parameters.
* We need a parameter-efficient method that calibrates model weights to represent our context-oriented ticket data before training.

The **SFT/CorDA Component** solves this by implementing **CorDA (Context-Oriented Decomposition Adaptation)**. It calculates weight parameter covariance on a calibration set, performs Singular Value Decomposition (SVD), and initializes adapters to target the most contextually relevant parameter subspaces.

---

## What (Structure & Layout)
This component holds training configs, tokenizers, evaluation logs, and SFT trainers:
* **`train_corda.py`:** The primary training script that loads the model, runs covariance calibration, runs SVD initialization, and trains the PEFT model.
* **`train_config.yml`:** Configuration specifying the base model path, learning rates, epochs, and LoRA parameters.
* **`data_tokenizer.py`:** Preprocesses and tokenizes training datasets into formatted instruction-response pairs.
* **`data_collate.py` & `collator_diagnosis.py`:** Collation scripts that prepare training batches and verify response sequence lengths.
* **`merge_lora.py`:** Helper that merges the trained LoRA adapter weights back into the base model parameters for deployment.
* **`corda_eval.py` & `corda_evaluation.py`:** Performs post-training inference benchmarks to evaluate accuracy and model perplexity.
* **`ufone_synthetic_1000.jsonl`:** The domain-specific training dataset containing 1,000 synthetic ticket conversations.

---

## How (Implementation & Flow)

### 1. The CorDA Training Flow
1. **Calibration Data Collection (`train_corda.py`):** Loads 128 context-oriented samples from the training dataset.
2. **Covariance Profiling (`run_model`):** Performs forward passes on these 128 samples, monitoring activations in the self-attention and MLP layers to compute weight parameter covariance matrices.
3. **Context-Oriented Decomposition (`preprocess_corda`):** Applies SVD (Singular Value Decomposition) to isolate parameters representing the specific diagnostic context.
4. **Adapter Initialization:** Initializes LoRA matrices $A$ and $B$ using the principal singular vectors from the SVD, locking adaptation focus to these parameters.
5. **Supervised Fine-Tuning:** Trains the adapter weights using Hugging Face's `SFTTrainer` over the remaining dataset epochs.
6. **Evaluation & Consolidation:** Evaluates the model via `corda_eval.py` and merges the weights back into the base model using `merge_lora.py`.

### 2. Key Parameter Choices
* **LoRA Rank (r=8 or 16):** Defines the dimension of the low-rank updates.
* **Target Modules:** Targets the key attention projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`) and gate layers (`gate_proj`, `up_proj`, `down_proj`).
