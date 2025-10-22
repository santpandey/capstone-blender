import json
import os
from typing import List, Optional, Tuple

import numpy as np
import tiktoken
from transformers.tokenization_utils import AddedToken, PreTrainedTokenizer
from transformers.utils import logging, hf_bucket_url, cached_path

logger = logging.get_logger(__name__)

VOCAB_FILES_NAMES = {"vocab_file": "qwen.tiktoken"}

def _get_vocab_file_path(pretrained_model_name_or_path, vocab_file) -> Optional[str]:
    if os.path.exists(vocab_file):
        return vocab_file
    try:
        url = hf_bucket_url(pretrained_model_name_or_path, filename=vocab_file)
        return cached_path(url, cache_dir=os.environ.get("TRANSFORMERS_CACHE"))
    except Exception as e:
        logger.error(f"Could not download {vocab_file} from Hub: {e}")
        return None

class Qwen2Tokenizer(PreTrainedTokenizer):
    """Qwen2Tokenizer"""

    model_input_names = ["input_ids", "attention_mask"]
    vocab_files_names = VOCAB_FILES_NAMES

    def __init__(self, vocab_file, errors="replace", **kwargs):
        self.errors = errors
        resolved_vocab_file = _get_vocab_file_path(kwargs.get('name_or_path', 'FreedomIntelligence/BlenderLLM'), vocab_file or VOCAB_FILES_NAMES['vocab_file'])
        if resolved_vocab_file is None:
            raise ValueError(f"Can't find a vocabulary file at path '{vocab_file}'.")

        self.mergeable_ranks = self._load_tiktoken_bpe(resolved_vocab_file)
        self.decoder = {v: k for k, v in self.mergeable_ranks.items()}
        super().__init__(**kwargs)

    def _load_tiktoken_bpe(self, tiktoken_bpe_file: str) -> dict[bytes, int]:
        with open(tiktoken_bpe_file, "rb") as f:
            contents = f.read()
        return {
            token: int(rank)
            for rank, token in enumerate(tiktoken.load.data_gym_to_mergeable_bpe_ranks(contents))
        }

    @property
    def vocab_size(self):
        return len(self.mergeable_ranks)

    def get_vocab(self):
        return self.mergeable_ranks

    def _tokenize(self, text, **kwargs):
        # This method is not directly used by the model generation but is required by the base class.
        return

    def _convert_token_to_id(self, token):
        return self.mergeable_ranks.get(token, self.mergeable_ranks.get(self.unk_token))

    def _convert_id_to_token(self, index):
        return self.decoder.get(index)

    def convert_tokens_to_string(self, tokens):
        return b"".join(tokens).decode(self.errors, errors=self.errors)

    def save_vocabulary(self, save_directory: str, filename_prefix: Optional[str] = None) -> Tuple[str]:
        # This is not needed for our use case
        return

    def build_inputs_with_special_tokens(self, token_ids_0, token_ids_1=None):
        return token_ids_0
