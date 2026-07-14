"""=== COLLATOR DIAGNOSTIC TEST ===

🚨 WHAT THE MODEL IGNORES (Prompt & Formatting):
<s><|user|>
YouareaNetworkSupportagent,answerthequestionbasedontheprovidedinformation.Ifyoudon'tknowtheanswer,sayyoudon'tknow.

Category:SupplementaryServices(RoutetoProvisioning)
Issue:CustomerwantstoactivateMissedCallAlertsbutsystemgiveserroronSamsungS23.</s>
<|assistant|></s>

✅ WHAT THE MODEL LEARNS (The Ufone Answer):
Pre-check:VerifyHLRprofileandactivesupplementaryservices.Decision:Notanetworkissue.Routeto:Provisioningteam."""

from trl import  DataCollatorForCompletionOnlyLM


def data_collator_diagnostic_test(dataset_for, tokenizer, collator):
    # Sample response template (you can adjust this based on your actual template)

    # 1. Grab the first 2 rows of your tokenized dataset as a standard Python list
    # 1. Grab the raw text string from your very first row
    sample_text = dataset_for[0]["text"]

    # 2. Tokenize JUST this one row for the test
    tokenized_sample = tokenizer(sample_text)

    # 3. Pass it to the collator (it expects a list of dictionaries)
    batch = collator([tokenized_sample])

    # 4. Extract the input IDs and Labels
    input_ids = batch["input_ids"][0]
    labels = batch["labels"][0]

    print("=== COLLATOR DIAGNOSTIC TEST ===")

    masked_tokens = []
    learned_tokens = []

    for token_id, label in zip(input_ids, labels):
        token_str = tokenizer.decode([token_id])
        
        if label == -100:
            masked_tokens.append(token_str)
        else:
            learned_tokens.append(token_str)

    print("\n🚨 WHAT THE MODEL IGNORES (Prompt & Formatting):")
    print("".join(masked_tokens))

    print("\n✅ WHAT THE MODEL LEARNS (The Ufone Answer):")
    print("".join(learned_tokens))