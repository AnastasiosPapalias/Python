# Fine-Tuning Guide — AI Doppelganger

How to train a model on your Messenger dataset and run it locally via Ollama.
Three paths, from easiest to most powerful.

---

## Overview

| Path | GPU needed | Cost | Quality | Setup |
|---|---|---|---|---|
| **A. OpenAI API** | None | ~$1–5 per run | Good (GPT-4o-mini) | Easiest |
| **B. Google Colab + Unsloth** | Free T4/A100 (Colab) | Free or ~$10 | Best (Llama 3 8B) | Medium |
| **C. Local (ROCm / CUDA)** | Yes (AMD or NVIDIA) | Free | Best | Hard |

**Recommended starting point: Path A** — validate data quality cheaply, then move to B for an open-source model you can run locally via Ollama.

---

## Step 0 — Generate the Training Data

Run these two scripts in order:

```bash
# Step 1: Extract both sides of your conversations
python extract_messenger_personality.py \
  --input  "/path/to/facebook-export/messages" \
  --output "./my-dataset" \
  --my-name "Your Facebook Name"

# Step 2: Build training pairs
python build_training_pairs.py \
  --db      "./my-dataset/messages.sqlite" \
  --output  "./my-dataset/training_pairs_openai.jsonl" \
  --system-prompt "./my-system-prompt.md" \
  --format  openai \
  --context-turns 3 \
  --max-gap-minutes 120 \
  --split
```

This produces:
- `training_pairs_openai_train.jsonl` — 90% of pairs for training
- `training_pairs_openai_val.jsonl`   — 10% of pairs for validation

---

## Path A — OpenAI Fine-Tuning

Cheapest way to test. Produces a GPT-4o-mini model fine-tuned on your data.

### Prerequisites
```bash
pip install openai
export OPENAI_API_KEY="sk-..."
```

### Validate the data format
```bash
python - <<'EOF'
import json
path = "./my-dataset/training_pairs_openai_train.jsonl"
errors = 0
with open(path) as f:
    for i, line in enumerate(f):
        try:
            obj = json.loads(line)
            assert "messages" in obj
            for m in obj["messages"]:
                assert "role" in m and "content" in m
        except Exception as e:
            print(f"Line {i}: {e}")
            errors += 1
print(f"Validated. Errors: {errors}")
EOF
```

### Upload and train
```python
from openai import OpenAI
client = OpenAI()

train_file = client.files.create(
    file=open("./my-dataset/training_pairs_openai_train.jsonl", "rb"),
    purpose="fine-tune"
)
val_file = client.files.create(
    file=open("./my-dataset/training_pairs_openai_val.jsonl", "rb"),
    purpose="fine-tune"
)
print(f"Train file: {train_file.id}")
print(f"Val file:   {val_file.id}")

job = client.fine_tuning.jobs.create(
    training_file=train_file.id,
    validation_file=val_file.id,
    model="gpt-4o-mini-2024-07-18",
    hyperparameters={"n_epochs": 3},
    suffix="my-doppelganger"
)
print(f"Job ID: {job.id}")
print(f"Status: {job.status}")
```

### Monitor
```python
job = client.fine_tuning.jobs.retrieve(job.id)
print(job.status, job.fine_tuned_model)

for event in client.fine_tuning.jobs.list_events(job.id).data:
    print(event.message)
```

### Test
```python
model_id = "ft:gpt-4o-mini-2024-07-18:my-doppelganger:..."

response = client.chat.completions.create(
    model=model_id,
    messages=[{"role": "user", "content": "Hey, how are you?"}]
)
print(response.choices[0].message.content)
```

### Cost estimate
- GPT-4o-mini: ~$0.30 / 1M training tokens
- At ~50K pairs × ~100 tokens avg = ~5M tokens → ~$1.50

---

## Path B — Google Colab + Unsloth (Recommended for open-source)

Fine-tune Llama 3 8B on a free Colab GPU. Result: a model you own and can run locally via Ollama.

### Step 1 — Generate ShareGPT format pairs
```bash
python build_training_pairs.py \
  --db      "./my-dataset/messages.sqlite" \
  --output  "./my-dataset/training_pairs_sharegpt.jsonl" \
  --system-prompt "./my-system-prompt.md" \
  --format  sharegpt \
  --context-turns 4 \
  --split
```

### Step 2 — Upload to Google Drive
Upload `training_pairs_sharegpt_train.jsonl` and `training_pairs_sharegpt_val.jsonl` to your Google Drive.

### Step 3 — Run Unsloth in Colab

```python
# In a Colab notebook:
!pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install --no-deps trl peft accelerate bitsandbytes

from unsloth import FastLanguageModel
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Meta-Llama-3-8B-Instruct",
    max_seq_length = 2048,
    load_in_4bit = True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 42,
)

from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

dataset = load_dataset("json", data_files={
    "train": "/content/drive/MyDrive/training_pairs_sharegpt_train.jsonl",
    "test":  "/content/drive/MyDrive/training_pairs_sharegpt_val.jsonl",
})

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset["train"],
    dataset_text_field = "conversations",
    max_seq_length = 2048,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        num_train_epochs = 3,
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 10,
        output_dir = "outputs",
        optim = "adamw_8bit",
    ),
)
trainer.train()

model.save_pretrained_merged("my-doppelganger-llama3", tokenizer, save_method="merged_16bit")
```

### Step 4 — Import into Ollama
```bash
# Convert to GGUF
pip install llama-cpp-python
python -m llama_cpp.tools.convert --outtype q4_k_m my-doppelganger-llama3/ my-doppelganger.gguf

# Create Modelfile
cat > Modelfile << 'EOF'
FROM ./my-doppelganger.gguf
SYSTEM """[paste your system prompt here]"""
PARAMETER temperature 0.8
PARAMETER top_p 0.9
EOF

ollama create my-doppelganger -f Modelfile
ollama run my-doppelganger
```

---

## Path C — Local GPU (ROCm / CUDA)

Run the same Unsloth training script from Path B locally instead of on Colab.

### NVIDIA (CUDA)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install "unsloth[cu121-ampere-torch230] @ git+https://github.com/unslothai/unsloth.git"
```

### AMD (ROCm on WSL2 / Linux)
```bash
# Install ROCm
wget https://repo.radeon.com/amdgpu-install/6.0.2/ubuntu/jammy/amdgpu-install_6.0.60002-1_all.deb
sudo apt install ./amdgpu-install_6.0.60002-1_all.deb
sudo amdgpu-install --usecase=rocm --no-dkms

# Verify
rocminfo | grep "gfx"

# Install PyTorch with ROCm
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7
```

**VRAM constraints:** 8GB VRAM → QLoRA 4-bit on models up to 7B params.

---

## Evaluating Results

Test with prompts that match the subject's typical conversations:

```python
test_prompts = [
    "Hey, how are you?",
    "What are you up to today?",
    "Can you help me with something?",
    "Long time no talk!",
]
```

The model should pass on:
- Correct language choice (matches what the subject typically uses)
- Message length (short if that's the subject's style)
- Absence of AI filler phrases ("Certainly!", "Great question!")
- Presence of characteristic verbal tics or expressions

---

## After Training

1. **Test locally** with Ollama
2. **Shorten the system prompt** — the fine-tuned model needs less instruction (style is in the weights now)
3. **Compare** system-prompt-only vs. fine-tuned on the same test prompts
4. **Iterate** — adjust training data filtering, epochs, or prompt format as needed
