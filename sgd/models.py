from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    filepath: str
    function_name: str
    old_code: str
    new_code: str


@dataclass
class DryRunInfo:
    ref_range: str
    num_files: int
    num_chunks: int
    chunks: List[Chunk]
    prompt: str
    estimated_tokens: int
