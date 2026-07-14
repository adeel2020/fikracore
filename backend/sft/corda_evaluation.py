import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from datasets import load_dataset
from tqdm import tqdm

# ==========================================
# 1. CONFIGURATION
# ==========================================
BASE_MODEL_ID = "/Users/adeelarshad/Notebooks/models/TinyLlama-1.1B-Chat-v1.0" # Replace with your exact base model
LORA_WEIGHTS_DIR = "./corda_out"            # The output directory from your SFTTrainer
TEST_DATA_PATH = "ufone_synthetic_test.jsonl" # A separate file the model hasn't seen!

# The exact prompt template we used for training
PROMPT_TEMPLATE = """
        <|system|>
        {system_prompt}</s>
        <|user|>
        {instruction}</s>
        <|assistant|>
        {answer}</s>
"""

# ==========================================
# 2. LOAD MODEL & TOKENIZER
# ==========================================
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    device_map="auto",
    torch_dtype=torch.float32 # Fast inference format
)

print("Merging trained LoRA weights...")
# This layers your fine-tuned Ufone knowledge on top of the base model
model = PeftModel.from_pretrained(base_model, LORA_WEIGHTS_DIR)
model.eval()

# ==========================================
# 3. PREPARE TEST DATA
# ==========================================
test_dataset = load_dataset("json", data_files=TEST_DATA_PATH, split="train")

def format_prompt_only(example):
    # We only build the prompt side here so the model can generate the answer
    instruction = f"Category: {example['category']}\nIssue: {example['question']}"
    # If you used a system prompt in training, add it above the instruction!
    prompt = PROMPT_TEMPLATE.format(instruction=instruction)
    return {"prompt": prompt, "ground_truth": example['answer']}

test_dataset = test_dataset.map(format_prompt_only)

# ==========================================
# 4. INFERENCE & EVALUATION LOOP
# ==========================================
exact_matches = 0
keyword_matches = 0
total = len(test_dataset)

print(f"\nStarting evaluation on {total} tickets...\n")

for i, row in enumerate(tqdm(test_dataset)):
    prompt = row["prompt"]
    ground_truth = row["ground_truth"]
    
    # Tokenize input
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Generate response
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            temperature=0.0,      # Strict deterministic output (no creativity)
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode and slice off the prompt to get just the model's new text
    input_length = inputs.input_ids.shape[1]
    generated_tokens = outputs[0][input_length:]
    prediction = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    
    # --- METRIC 1: Exact Match ---
    # Does it match the ground truth character-for-character?
    if prediction.lower() == ground_truth.lower():
        exact_matches += 1
        
    # --- METRIC 2: Routing Keyword Match (Fuzzy) ---
    # Even if the wording is slightly different, did it route to the right team?
    # Extract the team name from the ground truth (e.g., "Provisioning", "Core", "Radio")
    # This is a basic example—you can customize this logic!
    if "route to:" in ground_truth.lower():
        target_team = ground_truth.lower().split("route to:")[-1].strip()
        if target_team in prediction.lower():
            keyword_matches += 1
            
    # Print the first 5 examples to visually inspect the quality
    if i < 5:
        print(f"\n--- Ticket {i+1} ---")
        print(f"PROMPT:\n{prompt.replace('</s>', '').strip()}")
        print(f"\nPREDICTED: {prediction}")
        print(f"ACTUAL:    {ground_truth}")
        print("-" * 30)

# ==========================================
# 5. FINAL SCORES
# ==========================================
print("\n" + "="*40)
print("🎯 EVALUATION RESULTS")
print("="*40)
print(f"Total Tickets Tested: {total}")
print(f"Exact Match Accuracy: {(exact_matches / total) * 100:.2f}%")
print(f"Keyword Routing Accuracy: {(keyword_matches / total) * 100:.2f}%")
print("="*40)