import os

import matplotlib.pyplot as plt
from datasets import load_dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Trainer,
    TrainerCallback,
    TrainingArguments,
)

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_LENGTH = 512


class LossTrackerCallback(TrainerCallback):
    """Record train/eval loss so we can plot loss vs optimizer steps."""

    def __init__(self):
        self.train_steps: list[int] = []
        self.train_losses: list[float] = []
        self.eval_steps: list[int] = []
        self.eval_losses: list[float] = []

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs:
            return
        step = state.global_step
        if "loss" in logs:
            self.train_steps.append(step)
            self.train_losses.append(float(logs["loss"]))
        if "eval_loss" in logs:
            self.eval_steps.append(step)
            self.eval_losses.append(float(logs["eval_loss"]))

    def save_plot(self, path: str) -> None:
        plt.figure(figsize=(8, 5))
        if self.train_steps:
            plt.plot(self.train_steps, self.train_losses, label="train loss")
        if self.eval_steps:
            plt.plot(
                self.eval_steps,
                self.eval_losses,
                marker="o",
                label="eval loss",
            )
        plt.xlabel("Optimizer steps")
        plt.ylabel("Loss")
        plt.title("Loss vs optimizer steps")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        print(f"Saved loss curve to {path}")


model_id = "LiquidAI/LFM2.5-350M-Base"
model = AutoModelForCausalLM.from_pretrained(model_id)

print(f"Model layers ({len(model.model.layers)}):")
lora_targets = set()
for i, layer in enumerate(model.model.layers):
    kind = "ATTN" if hasattr(layer, "self_attn") else "CONV"
    linear_names = [
        name.split(".")[-1]
        for name, module in layer.named_modules()
        if module.__class__.__name__ == "Linear" and name
    ]
    lora_targets.update(linear_names)
    print(f"  [{i:02d}] {kind:4s}  linears={linear_names}")

print(f"\nLoRA target_modules candidates: {sorted(lora_targets)}")

tokenizer = AutoTokenizer.from_pretrained(model_id)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    model.config.pad_token_id = tokenizer.pad_token_id

# ── dataset loading ──────────────────────────────────────────────────────

train_dataset = load_dataset(
    "json",
    data_files=os.path.join(HERE, "data", "train.chat.jsonl"),
    split="train",
)
val_dataset = load_dataset(
    "json",
    data_files=os.path.join(HERE, "data", "val.chat.jsonl"),
    split="train",
)

# ── tokenization ─────────────────────────────────────────────────────────


def _format_chat(messages: list[dict], add_generation_prompt: bool = False) -> str:
    try:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=add_generation_prompt,
        )
    except Exception:
        parts = [f"<|{m['role']}|>\n{m['content']}" for m in messages]
        text = "\n".join(parts)
        if add_generation_prompt:
            return text + "\n<|assistant|>\n"
        return text + tokenizer.eos_token


def tokenize_fn(examples):
    """Mask prompt tokens so loss is only on the assistant actions JSON."""
    input_ids_batch = []
    labels_batch = []
    attention_batch = []
    for msgs in examples["messages"]:
        prompt_msgs = msgs[:-1]
        full_text = _format_chat(msgs, add_generation_prompt=False)
        prompt_text = _format_chat(prompt_msgs, add_generation_prompt=True)
        full = tokenizer(
            full_text, truncation=True, max_length=MAX_LENGTH, padding=False
        )
        prompt = tokenizer(
            prompt_text, truncation=True, max_length=MAX_LENGTH, padding=False
        )
        ids = full["input_ids"]
        prompt_len = min(len(prompt["input_ids"]), len(ids))
        labels = [-100] * prompt_len + ids[prompt_len:]
        input_ids_batch.append(ids)
        labels_batch.append(labels)
        attention_batch.append(full["attention_mask"])
    return {
        "input_ids": input_ids_batch,
        "labels": labels_batch,
        "attention_mask": attention_batch,
    }


tokenized_train = train_dataset.map(
    tokenize_fn, batched=True, remove_columns=train_dataset.column_names
)
tokenized_val = val_dataset.map(
    tokenize_fn, batched=True, remove_columns=val_dataset.column_names
)

data_collator = DataCollatorForSeq2Seq(
    tokenizer, pad_to_multiple_of=8, padding=True
)

# ── LoRA ─────────────────────────────────────────────────────────────────

peft_config = LoraConfig(
    target_modules="all-linear",
    task_type=TaskType.CAUSAL_LM,
    inference_mode=False,
    r=16,
    lora_alpha=64,
    lora_dropout=0.1,
)

peft_model = get_peft_model(model, peft_config)
peft_model.print_trainable_parameters()

# ── training ─────────────────────────────────────────────────────────────

loss_tracker = LossTrackerCallback()

training_args = TrainingArguments(
    output_dir=os.path.join(HERE, "output"),
    learning_rate=3e-4,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    gradient_accumulation_steps=8,
    num_train_epochs=2,
    weight_decay=0.01,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    logging_steps=1,
    logging_strategy="steps",
    report_to="none",
)

trainer = Trainer(
    model=peft_model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_val,
    data_collator=data_collator,
    callbacks=[loss_tracker],
)

trainer.train()

os.makedirs(os.path.join(HERE, "output"), exist_ok=True)
loss_tracker.save_plot(os.path.join(HERE, "output", "loss_curve.png"))

peft_model.save_pretrained(os.path.join(HERE, "output", "final"))
