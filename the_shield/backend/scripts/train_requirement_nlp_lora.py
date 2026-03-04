"""
LoRA fine-tuning script for RequiMind NLP tasks.

Dataset format (JSONL):
{"instruction": "...", "input": "...", "output": "..."}
"""

from __future__ import annotations

import argparse
from pathlib import Path

from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a local NLP model with LoRA for RequiMind.")
    parser.add_argument(
        "--model-name",
        default="microsoft/Phi-3.5-mini-instruct",
        help="Base model checkpoint.",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to JSONL dataset with instruction/input/output fields.",
    )
    parser.add_argument(
        "--output-dir",
        default="./outputs/phi35-requimind-lora",
        help="Output directory for LoRA adapter and tokenizer.",
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--max-seq-len", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def format_example(example: dict) -> dict:
    instruction = (example.get("instruction") or "").strip()
    inp = (example.get("input") or "").strip()
    output = (example.get("output") or "").strip()
    prompt = (
        "<|system|>\n"
        "You are a requirement engineering NLP assistant.\n"
        "<|user|>\n"
        f"Instruction: {instruction}\n"
        f"Input: {inp}\n"
        "<|assistant|>\n"
        f"{output}"
    )
    return {"text": prompt}


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    raw = load_dataset("json", data_files=str(dataset_path), split="train")
    split = raw.train_test_split(test_size=0.1, seed=args.seed)

    train_data = split["train"].map(format_example, remove_columns=split["train"].column_names)
    eval_data = split["test"].map(format_example, remove_columns=split["test"].column_names)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        trust_remote_code=True,
        device_map="auto",
    )

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )

    train_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        num_train_epochs=args.epochs,
        logging_steps=10,
        eval_steps=100,
        save_steps=100,
        save_total_limit=2,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        bf16=False,
        fp16=True,
        report_to=[],
        seed=args.seed,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=train_args,
        train_dataset=train_data,
        eval_dataset=eval_data,
        peft_config=peft_config,
        max_seq_length=args.max_seq_len,
        dataset_text_field="text",
    )
    trainer.train()

    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"Training complete. Adapter saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
