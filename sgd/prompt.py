from typing import Dict, List

from sgd.models import Chunk


def build_prompt(chunks: List[Chunk], lang: str = "en") -> str:
    files: Dict[str, List[Chunk]] = {}
    for chunk in chunks:
        files.setdefault(chunk.filepath, []).append(chunk)

    sections: list[str] = []
    for filepath, file_chunks in files.items():
        sections.append(f"### File: {filepath}")
        sections.append("")
        for i, chunk in enumerate(file_chunks, 1):
            if chunk.function_name:
                sections.append(f"#### Region: {chunk.function_name}")
            sections.append("--- Before ---")
            sections.append(chunk.old_code or "(no code removed)")
            sections.append("")
            sections.append("--- After ---")
            sections.append(chunk.new_code or "(no code added)")
            sections.append("")

    changes_text = "\n".join(sections).strip()

    lang_instruction = ""
    if lang != "en":
        lang_instruction = f"\nRespond in {lang}."

    prompt = f"""You are an expert code reviewer. Summarize the following git diff in plain English.

Changes across {len(files)} files ({len(chunks)} code regions):

{changes_text}

Generate a structured markdown summary with these sections:
## Summary
A 2-3 sentence overview of what changed overall and why.

## Changes

### `filepath`
- Bullet point per logical change in this file

Stay concise. Use plain English. No technical jargon unless essential.{lang_instruction}"""

    return prompt


def estimate_tokens(text: str) -> int:
    return len(text) // 4
