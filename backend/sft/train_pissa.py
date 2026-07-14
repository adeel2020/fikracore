import yaml
import argparse
import os, torch

print("\n========== ENV ==========")
print("Python:", os.sys.version)
print("Torch:", torch.__version__)
print("Device:", torch.device("cpu"))
print("=========================\n")


from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import SFTConfig, SFTTrainer
from peft import LoraConfig

# -------------------------
# CONFIG
# -------------------------
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
)

# -------------------------
# LORA CONFIGURATION
# -------------------------
# SFTTrainer will handle LoRA wrapping, casting, and preparation automatically
lora_cfg = LoraConfig(
    r=cfg["lora"]["r"],
    lora_alpha=cfg["lora"]["alpha"],
    lora_dropout=cfg["lora"]["dropout"],
    target_modules=cfg["lora"]["target_modules"],
    bias="none",
    task_type="CAUSAL_LM",
    use_rslora=True,  # RSLoRA is a more stable variant that prevents divergence in 1B models
    init_lora_weights = "pissa"
)

# -------------------------
# DATASET
# -------------------------
dataset_cfg = cfg["datasets"][0]

dataset = load_dataset("json", data_files=dataset_cfg["path"],
    split="train",
)


import pandas as pd

def print_sample(example, instruction_field, output_field):

    print("\n========== SAMPLE ==========")

    print(f"{instruction_field}:")
    print(example[instruction_field])

    print("\n→")

    print(f"{output_field}:")
    print(example[output_field][:100])

    print("=" * 28 + "\n")

from data_tokenizer import build_tokenizer_dataset

dataset_for, dataset_tok = build_tokenizer_dataset(dataset, tokenizer, cfg)

dataset_for[0]['prompt']
dataset_for[0]['completion']
tokenizer.decode(dataset_tok[0]['input_ids'])
# -------------------------
# TRAINING CONFIGURATION
# -------------------------
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
# SAVE LORA & TOKENIZER
# -------------------------
trainer.save_model(cfg["output_dir"])
tokenizer.save_pretrained(cfg["output_dir"])