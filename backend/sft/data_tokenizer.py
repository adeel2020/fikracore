def build_tokenizer_dataset(dataset, tokenizer, cfg):
    """
    Prepares a dataset for SFTTrainer with manual -100 masking.
    NOTE: You must set packing=False in your SFTTrainer when using this!
    """
    
    dataset_type = cfg["datasets"][0]["type"]
    system_field = dataset_type.get("system_prompt", "")
    category_field = dataset_type["field_category"]       
    instruction_field = dataset_type["field_instruction"] 
    output_field = dataset_type["field_output"]           
    prompt_format = dataset_type["format"]

    # -------------------------
    # 1. FORMAT STEP
    # -------------------------
    def format_example(example):
        category = example[category_field]
        question = example[instruction_field]
        answer = example[output_field]

        user_prompt = (
            f"Category: {category}\n"
            f"Issue: {question}"
        )
        # USER PROMPT ONLY (for inference / evaluation)
        prompt_message = [
            {"role": "system", "content": system_field},
            {"role": "user", "content": user_prompt}
        ]
        # sysprompt = f"{system_field}"
        # instruction = f"{user_prompt}"
        # answer = f"{answer}"        
        
        # prompt = prompt_format.format(system_prompt=sysprompt,  instruction=instruction, answer="")
        # text = prompt_format.format(system_prompt=sysprompt,  instruction=instruction, answer=answer)
        
        prompt = tokenizer.apply_chat_template(
            prompt_message,
            tokenize=False,
            add_generation_prompt=False  # IMPORTANT
        )

        # FULL TRAINING TEXT
        answer_message = [
            {"role": "assistant", "content": answer}
        ]

        completion = tokenizer.apply_chat_template(
            answer_message,
            tokenize=False,
            add_generation_prompt=False
        )
        
        return {
            "completion": completion,
            "prompt": prompt,
            "text": prompt + completion
        }

    formated = dataset.map(format_example, desc="Formatting prompts")

    # -------------------------
    # 2. TOKENIZATION STEP
    # -------------------------
    def tokenize(example):
        max_length = cfg["max_seq_length"]

        # Tokenize the full text (Prompt + Answer)
        completion_tok = tokenizer(
            example["completion"],
            truncation=True,
            padding=False, # MUST pad here since we aren't packing!
            max_length=max_length,
        )
        
        # Tokenize just the prompt to find its exact length
        prompt_tok = tokenizer(
            example["prompt"],
            truncation=True,
            padding=False,        # No padding needed, just counting tokens
            max_length=max_length,
        )   
        # 2. Extract the Python lists
        prompt_ids = prompt_tok["input_ids"]
        completion_ids = completion_tok["input_ids"]
        
        prompt_mask = prompt_tok["attention_mask"]
        completion_mask = completion_tok["attention_mask"]
        
        # 3. Concatenate (Glue them together)
        input_ids = prompt_ids + completion_ids
        attention_mask = prompt_mask + completion_mask
        
        # input_ids = full["input_ids"]
        # attention_mask = full["attention_mask"]
        labels = input_ids.copy()

        # Mask prompt tokens and padding tokens with -100
        # prompt_len = len(prompt_tok["input_ids"])
        
        # # Mask the prompt
        # labels[:prompt_len] = [-100] * prompt_len
        # # Mask the padding tokens at the end (so loss ignores empty space)
        # for i in range(len(input_ids)):
        #     if input_ids[i] == tokenizer.pad_token_id:
        #         labels[i] = -100

        # THIS RETURN MUST BE UNCOMMENTED AND PROPERLY INDENTED
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels
        }

    # Notice this is OUTSIDE the tokenize function definition!
    tokenized = formated.map(tokenize, desc="Tokenizing and Masking")

    # -------------------------
    # 3. FINAL FORMAT
    # -------------------------
    tokenized.set_format(
        type="torch",
        columns=["input_ids", "attention_mask", "labels"] # Labels MUST be included here!
    )

    return formated, tokenized