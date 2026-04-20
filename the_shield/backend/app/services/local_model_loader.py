import os
from typing import Optional, Any
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    _HAS_TORCH = True
except ImportError:
    torch = None
    AutoModelForCausalLM = None
    AutoTokenizer = None
    PeftModel = None
    _HAS_TORCH = False

from app.core.settings import get_settings


class LocalModelLoader:
    _instance = None
    _model = None
    _tokenizer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalModelLoader, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        if not _HAS_TORCH:
            print("Warning: Local ML dependencies (torch, transformers, peft) are not installed. Local mode will not work.")
            return

        if self._model is not None:
            return

        settings = get_settings()
        model_name = settings.ollama_model or "microsoft/Phi-3.5-mini-instruct"
        adapter_path = os.path.join("outputs", "phi35-requimind-lora")

        try:
            print(f"Loading local base model: {model_name}...")
            self._tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            base_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                device_map="auto",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            )

            if os.path.exists(adapter_path):
                print(f"Loading LoRA adapter from: {adapter_path}...")
                self._model = PeftModel.from_pretrained(base_model, adapter_path)
            else:
                print("No adapter found. Using base model.")
                self._model = base_model

            self._model.eval()
        except Exception as e:
            print(f"Error loading local model: {e}")
            self._model = None
            self._tokenizer = None

    def generate(self, instruction: str, input_text: str, max_new_tokens: int = 512) -> Optional[str]:
        if not _HAS_TORCH or not self._model or not self._tokenizer:
            return None


        prompt = (
            "<|system|>\n"
            "You are a requirement engineering NLP assistant.\n"
            "<|user|>\n"
            f"Instruction: {instruction}\n"
            f"Input: {input_text}\n"
            "<|assistant|>\n"
        )

        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self._tokenizer.pad_token_id,
            )

        response = self._tokenizer.decode(outputs[0][len(inputs["input_ids"][0]):], skip_special_tokens=True)
        return response.strip()

def get_local_model_loader() -> LocalModelLoader:
    loader = LocalModelLoader()
    # Lazy init on first use if needed, or caller can manually init
    return loader
