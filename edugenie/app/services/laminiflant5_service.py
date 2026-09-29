import logging
import os
from typing import Optional

# Prevent OpenMP runtime conflict on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

logger = logging.getLogger("edugenie.lamini")

DEFAULT_LOCAL_MODEL = os.getenv("LAMINI_MODEL", "MBZUAI/LaMini-Flan-T5-248M")


class LaMiniFlanT5Service:
    """Service wrapper for running LaMini-Flan-T5 locally with Hugging Face Transformers & PyTorch.

    Implements lazy-loading as a singleton to avoid re-downloading or reloading model weights on each request.
    Gracefully handles hardware limitations and memory constraints without crashing the app.
    """

    def __init__(self, model_name: str = DEFAULT_LOCAL_MODEL):
        self.model_name = model_name
        self._tokenizer = None
        self._model = None
        self._is_loaded = False
        self._load_error = None

    def is_loaded(self) -> bool:
        return self._is_loaded

    def get_status(self) -> dict:
        return {
            "model_name": self.model_name,
            "is_loaded": self._is_loaded,
            "error": self._load_error
        }

    def _ensure_loaded(self):
        """Loads model and tokenizer lazily on first invocation."""
        if self._is_loaded:
            return

        if self._load_error:
            raise RuntimeError(f"LaMini-Flan-T5 is unavailable: {self._load_error}")

        try:
            logger.info(f"Loading local model '{self.model_name}'... (This may take a moment on first run)")
            import torch
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using compute device: {device}")

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self._model.to(device)
            self._model.eval()

            self._device = device
            self._is_loaded = True
            self._load_error = None
            logger.info(f"Successfully loaded {self.model_name} on {device}.")
        except Exception as e:
            self._load_error = str(e)
            logger.error(f"Failed to load LaMini-Flan-T5 local model: {e}")
            raise RuntimeError(
                f"LaMini-Flan-T5 could not be loaded due to a local resource/environment limitation ({e}). "
                "You can continue using the Google Gemini model in the meantime."
            )

    def generate_text(self, prompt: str, max_length: int = 512, min_length: int = 30) -> str:
        """Generates text using the local LaMini-Flan-T5 model."""
        self._ensure_loaded()

        import torch

        try:
            inputs = self._tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self._device)

            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_length=max_length,
                    min_length=min_length,
                    num_beams=2,
                    early_stopping=True,
                    no_repeat_ngram_size=2
                )

            result = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            return result.strip()
        except Exception as e:
            logger.error(f"LaMini-Flan-T5 generation error: {e}")
            raise RuntimeError(f"Local model generation failed: {e}")


# Global singleton instance
lamini_service = LaMiniFlanT5Service()
