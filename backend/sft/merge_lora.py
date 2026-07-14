import json
import re
import numpy as np
import torch
import os
import yaml
import argparse
import sys
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel, PeftConfig
from sklearn.metrics import accuracy_score, f1_score
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu
from peft.tuners.lora.corda import preprocess_corda
from peft import LoraConfig
from peft.tuners.lora.config import CordaConfig
from data_tokenizer import build_tokenizer_dataset
from datasets import load_dataset
from tqdm import tqdm

# -------------------------
# LOAD CONFIG
# -------------------------
sys.argv = [
    "script.py",
    "--config", "train_config.yml",
]
parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
args = parser.parse_args()

cfg = yaml.safe_load(open(args.config))

# Paths from YAML config
BASE_MODEL_ID = cfg["base_model"]
LORA_WEIGHTS_DIR = cfg["output_dir"]
MERGED_DIR = cfg.get("merged_dir", "./sft_merged_model")
TEST_DATA_PATH = "ufone_synthetic_1000.jsonl"

print(f"Base Model: {BASE_MODEL_ID}")
print(f"LoRA Weights Dir: {LORA_WEIGHTS_DIR}")
print(f"Target Merged Dir: {MERGED_DIR}")

# -------------------------
# DETERMINE ADAPTER TYPE
# -------------------------
adapter_config_path = os.path.join(LORA_WEIGHTS_DIR, "adapter_config.json")
is_corda = False

if os.path.exists(adapter_config_path):
    try:
        with open(adapter_config_path, "r") as f:
            adapter_cfg = json.load(f)
            init_weights = adapter_cfg.get("init_lora_weights")
            print(f"Detected adapter init_lora_weights: {init_weights}")
            if init_weights == "corda":
                is_corda = True
    except Exception as e:
        print(f"Warning: Could not read adapter config ({e}). Defaulting to standard LoRA/PiSSA loading.")
else:
    print("Warning: adapter_config.json not found. Defaulting to standard LoRA/PiSSA loading.")

# Load Tokenizer
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)

# -------------------------
# LOAD BASE MODEL
# -------------------------
print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    device_map="cpu",
    torch_dtype=torch.float32,
)

# -------------------------
# CONDITIONAL CORDA PREPROCESSING
# -------------------------
if is_corda:
    print("CorDA adapter detected. Running covariance preprocessing...")
    dataset = load_dataset("json", data_files=TEST_DATA_PATH, split="train")
    dataset_for, dataset_tok = build_tokenizer_dataset(dataset, tokenizer, cfg)

    @torch.no_grad()
    def run_model():
        base_model.eval()
        for batch in tqdm(dataset_tok.select(range(128)), 
                          total=128,
                          desc="Computing Covariance"):
            inputs = {
                "input_ids": batch["input_ids"].unsqueeze(0).to(base_model.device),
                "attention_mask": batch["attention_mask"].unsqueeze(0).to(base_model.device),
            }
            base_model(**inputs)

    corda_cfg = CordaConfig(
        corda_method="ipm",
        verbose=True,
    )

    lora_cfg = LoraConfig(
        r=cfg["lora"]["r"],
        lora_alpha=cfg["lora"]["alpha"],
        lora_dropout=cfg["lora"]["dropout"],
        target_modules=cfg["lora"]["target_modules"],
        bias="none",
        task_type="CAUSAL_LM",
        init_lora_weights="corda",
        corda_config=corda_cfg,
    )

    preprocess_corda(base_model, lora_cfg, run_model=run_model)
else:
    print("Standard LoRA/PiSSA adapter detected. Bypassing covariance preprocessing.")

# -------------------------
# LOAD & MERGE PEFT MODEL
# -------------------------
print("Loading LoRA adapter...")
model = PeftModel.from_pretrained(
    base_model,
    LORA_WEIGHTS_DIR,     
    torch_dtype=torch.float32
)
model.eval()

print("Merging LoRA into base model...")
model = model.merge_and_unload()

print("\n========== MERGED ==========")
print("LoRA successfully merged into base model")
print("============================\n")

# -------------------------
# SAVE FULL MERGED MODEL
# -------------------------
print(f"Saving merged model to: {MERGED_DIR}")
model.save_pretrained(MERGED_DIR)
tokenizer.save_pretrained(MERGED_DIR)
print("Saved successfully!")
