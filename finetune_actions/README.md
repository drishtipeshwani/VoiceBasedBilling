# Action-array voice-command SFT dataset

Clone of `finetune/` that trains the same 350M LoRA recipe on a **sparse JSON
array of tagged actions** instead of a fixed all-keys response object. Leave
`finetune/` alone; this folder is the experiment.

One adapter, three tasks. Invoice, customer-ledger, and stock-item rows share
the same output family (a JSON array) but use different system prompts and
allowed actions. `meta.task` selects the prompt when chat files are built.

The dataset tooling is pure standard library. Training a LoRA adapter can reuse
`finetune/.venv` (same pins in `requirements.txt`).

## Regenerating data

```bash
python3 finetune_actions/generate_dataset.py --seed 20260817 --total 7300 \
  --customer-total 3600 --stock-total 3600
python3 finetune_actions/validate_dataset.py \
  finetune_actions/data/train.jsonl \
  finetune_actions/data/val.jsonl \
  finetune_actions/data/test.jsonl \
  --holdout finetune_actions/data/eval_handwritten.jsonl

python3 finetune_actions/to_chat.py finetune_actions/data/eval_handwritten.jsonl \
  -o finetune_actions/data/eval_handwritten.chat.jsonl
```

`--total` is invoice rows before split (default 7300, about 5700 train). Customer
and stock default to 3600 so each lands near 2500 train rows after dedupe at
the 8.4% / 8.4% val/test split. Each task is split on its own so adding
customer/stock does not reshuffle invoice rows.

Generation is seeded. The `.jsonl` splits are committed; `.chat.jsonl` files
are derived (they repeat the system prompt) and gitignored.

## Output shape

Always a JSON array, even for one command. Only the fields that utterance set:

```json
[{"action":"ADD_ITEM","name":"paneer","quantity":2,"pricePerItem":50}]
[{"action":"SET_NAME","name":"Rahul"},{"action":"SET_BALANCE","balanceAmount":1200}]
[{"action":"SET_NAME","name":"pens"},{"action":"SET_QUANTITY","quantity":10},{"action":"SET_COST","costPrice":20},{"action":"SET_SELLING","sellingPrice":35}]
[{"action":"INCOMPLETE"}]
```

Invoice `ADD_ITEM` may carry optional quantity / price / discount in one object.
Cross-item or mixed intents are multiple array elements. Customer and stock
drafts never copy omitted fields from the previous assistant JSON.

Row format:

```json
{"lastModified": null,
 "userInput": "add paneer add onion",
 "agentOutput": [{"action":"ADD_ITEM","name":"paneer"},{"action":"ADD_ITEM","name":"onion"}],
 "meta": {"conversationId": "combo-3", "turnIndex": 0, "tags": ["combo_two_add", "combo"], "task": "invoice"}}
```

`lastModified` is the previous actions array, or `null` on a cold start.

## Training

Same hyperparameters as `finetune/` (`r=16`, `alpha=64`, `lr=3e-4`, 2 epochs).
`finetune_llm.py` masks prompt tokens so loss is only on the assistant JSON.

```bash
finetune/.venv/bin/python finetune_actions/finetune_llm.py
finetune/.venv/bin/python finetune_actions/eval_llm.py
finetune/.venv/bin/python finetune_actions/merge_lora.py
```

Export to `.pte` follows the same ExecuTorch LFM2 recipe in `finetune/README.md`,
pointing at `finetune_actions/output/merged` instead.
