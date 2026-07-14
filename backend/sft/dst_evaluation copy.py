import torch
import time
import json
import re
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# --- 1. CONFIGURATION ---
base_path = "/Users/adeelarshad/Notebooks/models/TinyLlama-1.1B-Chat-v1.0"
adapter_path = "./lora_out"  # Path to your storytelling adapter
output_file = "story_eval_results.json"

# Prevent your i9 from thermal throttling during the batch run
torch.set_num_threads(4)

# Test prompts (Ensure these were NOT in your training data)
test_prompts = [
    "Write a short story about a detective who finds a clock that counts backwards.",
    "Tell a tale about a lost city underwater discovered by a robotic submarine.",
    "Write a story about a barista who accidentally invents a potion of truth."
]

# --- 2. LOAD MODEL ---
print("Loading model and adapter...")
tokenizer = AutoTokenizer.from_pretrained(base_path)
base_model = AutoModelForCausalLM.from_pretrained(base_path, torch_dtype=torch.float32)
model = PeftModel.from_pretrained(base_model, adapter_path)

# --- 3. METRIC FUNCTIONS ---
def calculate_diversity(text):
    """Calculates Lexical Diversity (Unique words / Total words).
       Higher is better. Low scores (< 0.4) indicate severe repetition."""
    # Strip punctuation and lowercase
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    unique_words = set(words)
    return round(len(unique_words) / len(words), 3)

# --- 4. EVALUATION LOOP ---
results = []
print(f"Starting evaluation of {len(test_prompts)} prompts...\n")

for i, prompt in enumerate(test_prompts):
    print(f"Generating Story {i+1}...")
    
    # Format according to your training data structure
    formatted_prompt = f"### Instruction:\n{prompt}\n\n### Response:\n"
    inputs = tokenizer(formatted_prompt, return_tensors="pt")
    
    start_time = time.time()
    
    # Generation settings optimized for storytelling (Higher temperature = more creative)
    outputs = model.generate(
        **inputs,
        max_new_tokens=250,
        temperature=0.8,
        top_p=0.9,
        repetition_penalty=1.15, # Helps prevent 1B models from looping
        do_sample=True,
    )
    
    end_time = time.time()
    
    # Decode and slice off the prompt to only evaluate the generated text
    input_length = inputs.input_ids.shape[1]
    generated_tokens = outputs[0][input_length:]
    generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    
    # Calculate metrics
    gen_time = end_time - start_time
    num_tokens = len(generated_tokens)
    tps = round(num_tokens / gen_time, 2)
    diversity = calculate_diversity(generated_text)
    
    # Store results
    results.append({
        "prompt": prompt,
        "generated_story": generated_text,
        "metrics": {
            "tokens_generated": num_tokens,
            "generation_time_sec": round(gen_time, 2),
            "tokens_per_second": tps,
            "lexical_diversity": diversity
        }
    })

# --- 5. SAVE RESULTS ---
with open(output_file, 'w') as f:
    json.dump(results, f, indent=4)

print(f"\nEvaluation complete! Results saved to {output_file}")
print("Average Tokens/Sec:", round(sum(r['metrics']['tokens_per_second'] for r in results) / len(results), 2))