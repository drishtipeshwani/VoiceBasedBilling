# Invoice voice-command SFT dataset

Training data for the on-device model that turns Indian English speech into
invoice edits.

The dataset tooling (`generate_dataset.py`, `validate_dataset.py`, `to_chat.py`
and friends) is pure standard library, no dependencies. Actually training a
LoRA adapter needs the environment below.

## Training environment

```bash
python3 -m venv finetune/.venv
finetune/.venv/bin/pip install -r finetune/requirements.txt
```

Installs `torch`, `transformers`, `peft`, `accelerate`, `datasets`.
Deliberately no `bitsandbytes` / QLoRA: LFM 350M and Hammer 1.5B are small
enough to LoRA-tune in fp32/bf16 without 4-bit quantization, and
bitsandbytes' Metal/MPS kernels are still an unaccelerated fallback rather
than real Metal support, so there's nothing to gain from it on this hardware.
Revisit if a larger base model ever enters the picture.

`finetune/.venv/` is gitignored; recreate it from `requirements.txt` rather
than expecting it to be committed.

**If `import datasets` fails with `ModuleNotFoundError: No module named
'_lzma'`**, the Python interpreter itself was compiled without `xz`
(liblzma) present on the machine — a pyenv build-order issue, not a
`datasets` version problem. Fix once, globally, then recreate the venv:

```bash
brew install xz
pyenv install 3.14.3 --force   # recompiles the interpreter against xz
```

Existing venvs pick this up automatically without recreating them, since a
venv references the base interpreter's `lib-dynload` at runtime rather than
copying it.

## Regenerate everything

```bash
python3 finetune/generate_dataset.py --seed 20260726 --total 4000
python3 finetune/validate_dataset.py 'finetune/data/train.jsonl' 'finetune/data/val.jsonl' 'finetune/data/test.jsonl' \
  --holdout finetune/data/eval_handwritten.jsonl

for split in train val test eval_handwritten; do
  python3 finetune/to_chat.py finetune/data/$split.jsonl -o finetune/data/$split.chat.jsonl
done
```

Generation is seeded, so the same seed gives byte-identical files. The
`.jsonl` splits are committed; the `.chat.jsonl` files are derived and are not,
since they repeat the system prompt on every row.

## Row format

```json
{"lastModified": null,
 "userInput": "add item pens quantity 10 price 50",
 "agentOutput": {"modifiedCompanyName": null, "...": "..."},
 "meta": {"conversationId": "single-3", "turnIndex": 0, "tags": ["add_item", "single"]}}
```

`lastModified` is the previous agent response, exactly what `HomeScreen` keeps
in `lastSuccessfulAgentResponseRef`. It is `null` on a cold start. `meta` is
bookkeeping for splitting and coverage; `to_chat.py` drops it.

`to_chat.py` emits the window the app actually builds, context assistant
message before the user turn included:

```
system    -> finetune/system_prompt.txt
assistant -> JSON.stringify(lastModified)   (omitted when null)
user      -> transcript
assistant -> target JSON                    (the training label)
```

## Files

| File | Role |
| --- | --- |
| `system_prompt.txt` | The training and inference prompt. `utils/invoiceSystemPrompt.ts` must match it; a jest test enforces that. |
| `schema.py` | Canonical key order, mirroring `types/agentResponse.ts`. |
| `pools.py` | Items, names, number and currency renderers, discount and date phrasings. |
| `noise.py` | ASR corruption, applied to transcripts only. |
| `intents.py` | One builder per command type, in named and pronoun forms. |
| `generate_dataset.py` | Assembles single-turn rows, conversations, negatives, splits. |
| `validate_dataset.py` | Schema, consistency and leakage checks plus coverage counts. |
| `to_chat.py` | Row to chat-window converter. |
| `data/eval_handwritten.jsonl` | 82 hand-written rows, never trained on. |
| `requirements.txt` | Pinned training dependencies for `finetune/.venv`. |

## What the data teaches

- **Digits or words.** Every number is spoken as digits, English words, or
  Indian magnitudes ("twelve hundred", "two fifty", "two lakh"); the target
  always carries the parsed value.
- **Model codes are item names.** In electronics and hardware the spoken
  identifier is often the model, not the product. "SL-253" reaches us as
  "sl 253", "sl253", "sl dash 253", "ess el 253" or "model number sl 253", and
  all of them normalise to `"SL-253"`. Codes also appear attached to a base
  word ("speaker SM-354"), and renaming one usually means correcting a misheard
  digit ("no it is SL-254").
- **Percent versus rupees.** "10 percent off" fills `discountPercent`,
  "20 rupees off" fills `discountAmount`, never both. Item scope and bill scope
  are separate fields with deliberately similar phrasing.
- **Dates pass through with a full month.** The model copies the phrase it heard,
  normalised so the day is digits with an ordinal suffix and any month is a full
  English name: "twenty fifth June", "June 25", and "25 Jun" all become
  `"25th June"`; "fourteenth" becomes `"14th"`. No calendar arithmetic, no ISO
  conversion. The app resolves it to DD/MM/YYYY.
- **Bad transcripts, correct targets.** "Make company name" arrives as "Main
  company name", "as" as "has", "price" as "prize", "quantity" as "quality".
  Number homophones are deliberately excluded, since those change the value
  rather than the wording.
- **Context resolution, in both directions.** Pronoun turns ("make its price
  20") must take the item name from `lastModified`. The counterweights: the
  same utterance with no context, or with a context that holds no item,
  resolves to `incompleteInput`; a turn that names a different item must use
  the spoken name.
- **The date-versus-quantity trap.** Right after item talk, "make it 14th" is a
  date and "make it 14" is a quantity. Both appear, and the noise layer is
  blocked from stripping the ordinal suffix on those rows.

## Adding to the dataset

Add vocabulary to `pools.py` or a phrasing to `intents.py`, then regenerate and
validate. `validate_dataset.py` fails on any row whose target names an item that
is neither audible in the transcript nor present in `lastModified`, which is the
check that catches a generator bug teaching the model to hallucinate items.

## On-device: merge LoRA and export `.pte`

`react-native-executorch` cannot load a PEFT adapter. Merge first, then
export the merged weights with ExecuTorch the same way Software Mansion
ships `LFM2_5_350M_QUANTIZED` (XNNPACK 8da4w).

```bash
finetune/.venv/bin/python finetune/merge_lora.py
```

Writes `finetune/output/merged/` (HF layout: `model.safetensors` + tokenizer).

The generic Hugging Face export paths do **not** work here.
`transformers`' `convert_and_export_with_cache` and `optimum-cli export
executorch` both assume a plain attention decoder with a static KV cache.
LFM2.5 is hybrid: most layers are short convolutions with their own cache,
which is why `optimum-executorch` does not list LFM2 among its supported
architectures and why ExecuTorch ships a dedicated `examples/models/lfm2`
recipe. Use that recipe.

Install ExecuTorch with pip in a **separate** venv. Do **not** install it
into `finetune/.venv`: it pulls its own torch (`>=2.12`) and would replace
the torch 2.13 that training and eval run on.

```bash
python3 -m venv ~/et-export
source ~/et-export/bin/activate
pip install executorch safetensors
```

ExecuTorch requires Python 3.10–3.13 (not 3.14). YAML configs ship in the
wheel; download `lfm2_5_350m_config.json` from the matching ExecuTorch
tag if it is missing.

The LFM2 export configs are YAML/JSON files that `export_llm` reads from
disk. Grab just that folder (no compile, no submodules):

```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/pytorch/executorch.git ~/executorch
cd ~/executorch
git sparse-checkout set examples/models/lfm2
```

Then convert the merged weights and export. Use the pip venv's `python`,
and pass absolute paths for the configs:

```bash
python -m executorch.examples.models.lfm2.convert_weights \
  /abs/path/to/voicebillingapp/finetune/output/merged \
  invoice_lfm2_5_350m.pth

# Eval-equivalent: no weight quantization, fp16, 2048 context.
# Matches finetune/eval_llm.py much more closely than 8da4w.
# Output is ~800MB (over the 512MB require() asset limit; load via https).
python -m executorch.extension.llm.export.export_llm \
  --config ~/executorch/examples/models/lfm2/config/lfm2_xnnpack_fp32.yaml \
  +base.model_class="lfm2_5_350m" \
  +base.params="$HOME/executorch/examples/models/lfm2/config/lfm2_5_350m_config.json" \
  +base.checkpoint="invoice_lfm2_5_350m.pth" \
  model.dtype_override=fp16 \
  +export.max_seq_length=2048 \
  +export.max_context_length=2048 \
  +export.output_name="invoice_lfm2_5_350m_fp16.pte"
```

The fp32 YAML has no `quantization:` block. `model.dtype_override=fp16`
overrides its default `fp32` cast so the file stays under 1GB (true fp32
is ~1.5GB). This is the same unquantized recipe Software Mansion ships
as `LFM2_5_350M`.

The default export window is **128 tokens**. The invoice system prompt plus
chat template is already ~184 tokens, so a 128-token `.pte` loads but fails
on `generate()` with an empty reply. Always set `max_seq_length` /
`max_context_length` as above.

A 4-bit `8da4w` export is smaller (~430MB) but destroys LoRA JSON quality
on this 350M adapter. Only use it if you need the `require()` asset path:

```bash
python -m executorch.extension.llm.export.export_llm \
  --config ~/executorch/examples/models/lfm2/config/lfm2_xnnpack_q8da4w.yaml \
  +base.model_class="lfm2_5_350m" \
  +base.params="$HOME/executorch/examples/models/lfm2/config/lfm2_5_350m_config.json" \
  +base.checkpoint="invoice_lfm2_5_350m.pth" \
  +export.max_seq_length=2048 \
  +export.max_context_length=2048 \
  +export.output_name="invoice_lfm2_5_350m_8da4w.pte"
```

Building from source (`./install_executorch.sh`) is only needed if pip
export fails, or you want extra backends (MLX, Core ML, Qualcomm).

`convert_weights` reads a single `model.safetensors`, so do not shard the
merged checkpoint when saving it.

The eval-equivalent `.pte` is ~800MB, over the 512MB `require()` limit.
Host it on Hugging Face (or any **https** URL). The tokenizer stays the
stock LFM2.5-350M one from Software Mansion.

```bash
# .env  (Expo inlines EXPO_PUBLIC_* at bundle time)
EXPO_PUBLIC_INVOICE_PTE=https://huggingface.co/drishti09/LFM-350M-VoiceBilling-FineTuned/resolve/main/invoice_lfm2_5_350m_fp16.pte
```

If `EXPO_PUBLIC_INVOICE_PTE` is unset, the app uses that Hugging Face URL
by default. `HomeScreen` then uses `INVOICE_SYSTEM_PROMPT_SHORT` (the
training prompt) instead of the long few-shot prompt. Rebuild/reload after
changing `.env`. The first device load downloads the `.pte` into the app
documents directory.
