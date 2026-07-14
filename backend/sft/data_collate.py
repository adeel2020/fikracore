
from torch.utils.data import DataLoader
from torch.nn.utils.rnn import pad_sequence
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained
def collate_fn(batch):
    # return {
    # "input_ids": torch.stack([x["input_ids"] for x in batch]),
    # "attention_mask": torch.stack([x["attention_mask"] for x in batch]),
    # "labels": torch.stack([x["labels"] for x in batch]),
    # }
    input_ids = pad_sequence(
        [x["input_ids"] for x in batch],
        batch_first=True,
        padding_value=tokenizer.pad_token_id
    )

    attention_mask = pad_sequence(
        [x["attention_mask"] for x in batch],
        batch_first=True,
        padding_value=0
    )
    labels = pad_sequence(
    [x["labels"] for x in batch],
    batch_first=True,
    padding_value=0
)

    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels" : labels
    }

 