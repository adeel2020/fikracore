import yaml
import argparse
import os, torch, sys
from tqdm import tqdm

print("\n========== ENV ==========")
print("Python:", os.sys.version)
print("Torch:", torch.__version__)
print("Device:", torch.device("cpu"))
print("=========================\n")


from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM



# -------------------------
# CONFIG
# -------------------------

sys.argv = [
    "script.py",
    "--config", "train_config.yml",
]
parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
args = parser.parse_args()

cfg = yaml.safe_load(open(args.config))

# -------------------------
# MODEL
# -------------------------
tokenizer = AutoTokenizer.from_pretrained(cfg["base_model"])

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    cfg["base_model"],
    torch_dtype=torch.float32,
    device_map="cpu",
)
model
# -------------------------
# DATASET
# -------------------------
dataset_cfg = cfg["datasets"][0]

dataset = load_dataset("json", data_files=dataset_cfg["path"],
    split="train",
)
dataset[0]
len(dataset[0])
from data_tokenizer import build_tokenizer_dataset
from collator_diagnosis import data_collator_diagnostic_test
from torch.utils.data import DataLoader

dataset_for, dataset_tok = build_tokenizer_dataset(dataset, tokenizer, cfg)
max_tokens = max(len(row) for row in dataset_tok["input_ids"])

print(f"The longest sequence in the dataset is: {max_tokens} tokens")

tokenizer.decode(dataset_tok[735]["input_ids"])
dataset_for[735]['completion']
dataset_for[735]['prompt']
total_tokens = len( dataset_tok[735]["input_ids"])
print(total_tokens/128/16*3)


# from data_collate import collate_fn
           
# shuffled_dataset = dataset_tok.shuffle(seed=42)
# corda_calibration_data = shuffled_dataset.select(range(128))
# corda_calibration_data[0]
# loader = DataLoader(
#         corda_calibration_data,
#         batch_size=128,
#         collate_fn=collate_fn,
#         shuffle=False)  

import pandas as pd

def print_sample(example, instruction_field, output_field):

    print("\n========== SAMPLE ==========")

    print(f"{instruction_field}:")
    print(example[instruction_field])

    print("\n→")

    print(f"{output_field}:")
    print(example[output_field][:100])

    print("=" * 28 + "\n")

print("\n========== SAMPLE FORMATTED TEXT ==========")
print(tokenizer.decode(dataset_tok[0]["input_ids"]))
print("==========================================\n")


if cfg["training"].get("gradient_checkpointing", False):
    model.gradient_checkpointing_enable()
    model.config.use_cache = False
    model.enable_input_require_grads()

# CPU safety
for param in model.parameters():
    if param.requires_grad:
        param.data = param.data.float()

model.to("cpu")

response_template = "\n<|assistant|>\n"

# data_collator_diagnostic_test(dataset_for, tokenizer, base_collator)
# -------------------------
# TRAINING CONFIGURATION
# -------------------------
from peft import LoraConfig, EvaConfig, get_peft_model
from peft.tuners.lora.config import CordaConfig
from peft.tuners.lora.corda import preprocess_corda
from peft.optimizers import create_loraplus_optimizer
import torch

# -------------------------
# CorDA/ LoRA CONFIGURATION
# -------------------------
# SFTTrainer will handle LoRA wrapping, casting, and preparation automatically

@torch.no_grad()
def run_model():
    model.eval()
    for batch in tqdm(dataset_tok.select(range(128)), 
                      total=128,
                      desc="Computing Covariance"):
        inputs = {
            "input_ids": batch["input_ids"].unsqueeze(0).to(model.device),
            "attention_mask": batch["attention_mask"].unsqueeze(0).to(model.device),
        }
        model(**inputs)
            
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

# Call `preprocess_corda` first to collect covariance matrix and build SVD result for model
# For more details, please refer to documentation of `preprocess_corda`

preprocess_corda(model, lora_cfg, run_model=run_model)
# use at line 186  # input = input.reshape(-1, input.shape[-1])

from trl import SFTConfig, SFTTrainer, DataCollatorForCompletionOnlyLM

# base_collator = DataCollatorForCompletionOnlyLM(
#     response_template="\n<|assistant|>",
#     tokenizer=tokenizer
# )
train_args = SFTConfig(
    output_dir=cfg["output_dir"],
    per_device_train_batch_size=cfg["training"]["micro_batch_size"],
    gradient_accumulation_steps=cfg["training"]["gradient_accumulation_steps"],
    num_train_epochs=cfg["training"]["epochs"],
    learning_rate=cfg["training"]["learning_rate"],
    logging_steps=1,
    logging_first_step=True,
    save_steps=10,
    optim="adafactor",
    fp16=False,
    bf16=False,
    use_cpu=True,
    report_to="none",
    disable_tqdm=False,
    # SFTTrainer specific configurations
    max_seq_length=cfg["max_seq_length"],
    packing=True,  # Set to True for better efficiency if needed
    )
# -------------------------
# INITIALIZE SFT TRAINER
# -------------------------
trainer = SFTTrainer(
    model=model,
    args=train_args,
    train_dataset=dataset_for,
    peft_config=lora_cfg,
)

# -------------------------
# TRAIN
# ------------------------- 
trainer.train()

# -------------------------
# MERGE LORA INTO BASE MODEL
# -------------------------

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

base_model_path = cfg["base_model"]
lora_path = cfg["output_dir"]      # <- where your trainer saved LoRA
output_path = cfg["merged_dir"]

# -------------------------
# SAVE LORA & TOKENIZER
# -------------------------
trainer.save_model(cfg["output_dir"])
tokenizer.save_pretrained(output_path)

print("\n========== MERGED ==========")
print("LoRA Training successfully completed")
print("============================\n")
