from transformers import pipeline
import torch

# 1. Initialize pipeline (Ensure tokenizer handles the GGUF/Quantized special tokens)
qa_pipeline = pipeline(
    "text-generation",
    model="./fp_merged",
    tokenizer="./fp_merged",
    device="cpu",
    torch_dtype=torch.float32
)

# 2. Define your QnA payload
context = """Match the relevant category. Answer the query ONLY based on training knowledge.
        if you don't know the answer, you should reply that you are not sure about the issue
        """

question = "How to buy the Air tickets."

# 3. Construct using the official Chat Template
messages = [
    {
        "role": "system", 
        "content": """You are a Telecom domain QA bot. Answer the question that are directly related to telcom services using {context}.
        For question not relevant to telecom. please reply "I don't know". Do not explain your reasoning. Do not say 'Based on the context'. Give a single, direct sentence response.
        """
    },
    {
        "role": "user", 
        "content": question
    }
]

# This automatically formats into TinyLlama's expected <|user|> / <|assistant|> structure
prompt = qa_pipeline.tokenizer.apply_chat_template(
    messages, 
    tokenize=False, 
    add_generation_prompt=True
)

# 4. Generate with strict constraints for 4-bit CPU execution
result = qa_pipeline(
    prompt,
    max_new_tokens=128,             # Keep it tight for QnA so it doesn't wander
    return_full_text=False,        # Hide the system/user prompt from the output
    
    # Critical parameters for quantized small models:
    do_sample=False,
    # temperature=0.1,               # Lower temperature keeps a 4-bit model focused
    # top_p=0.9,
    repetition_penalty=1.2,        # FORCES the model to break out of loops
    
    # # Stop execution immediately when TinyLlama outputs its end-of-string token
    # eos_token_id=qa_pipeline.tokenizer.eos_token_id,
    # pad_token_id=qa_pipeline.tokenizer.eos_token_id
)

print(result[0]["generated_text"].strip())