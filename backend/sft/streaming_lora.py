import torch
from threading import Thread
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from peft import PeftModel

# 1. Setup paths
base_path = "/Users/adeelarshad/Notebooks/models/TinyLlama-1.1B-Chat-v1.0"
adapter_path = "./lora_out"

# 2. Load Tokenizer and Model
tokenizer = AutoTokenizer.from_pretrained(base_path)
base_model = AutoModelForCausalLM.from_pretrained(base_path, torch_dtype=torch.float32)
model = PeftModel.from_pretrained(base_model, adapter_path)

def stream_response(user_input):
    # Format the prompt exactly like your training data
    prompt = f"### Instruction:\nYou are a creative story Teller.\n\n### Input:\n{user_input}\n\n### Response:\n"
    
    inputs = tokenizer(prompt, return_tensors="pt").to("cpu")
    
    # Initialize the streamer
    # skip_prompt=True ensures the CSR doesn't see the input repeated back
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    # Define generation arguments
    generation_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=1024,
        temperature=0.7,
        do_sample=True,
    )

    # Start generation in a separate thread
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    # Iterate through the streamer and print tokens as they arrive
    print("AI Agent: ", end="", flush=True)
    for new_text in streamer:
        print(new_text, end="", flush=True)
    print("\n")

# 3. Test it with one of your network issues
stream_response("Write a short story about a lost city:")