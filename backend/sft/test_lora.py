from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import torch

base_path = "/Users/adeelarshad/Notebooks/models/TinyLlama-1.1B-Chat-v1.0"

# 1. Load Base Model and Tokenizer (from the base path!)
tokenizer = AutoTokenizer.from_pretrained(base_path)
base_model = AutoModelForCausalLM.from_pretrained(base_path)

# 2. Load the Adapter
model = PeftModel.from_pretrained(base_model, "./lora_out")

# 3. Generate text manually (No pipeline needed)
prompt = "Write a short story about a lost city:"
inputs = tokenizer(prompt, return_tensors="pt")

# Generate the output
with torch.no_grad():

    outputs = model.generate(
        **inputs,
        max_new_tokens=1024,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
        repetition_penalty=1.1,
        pad_token_id=tokenizer.eos_token_id,
    )

print(tokenizer.decode(outputs[0], skip_special_tokens=True))