import json
from typing import Dict, List

from sgd.models import Chunk, DryRunInfo


def format_markdown(summary: str, chunks: List[Chunk], ref_range: str) -> str:
    lines = [
        f"# semantic-git-diff: {ref_range}",
        "",
        summary,
        "",
    ]
    return "\n".join(lines)


def format_json(summary: str, chunks: List[Chunk], ref_range: str) -> str:
    files: Dict[str, list] = {}
    for chunk in chunks:
        files.setdefault(chunk.filepath, []).append(
            {
                "function": chunk.function_name,
                "old_code": chunk.old_code,
                "new_code": chunk.new_code,
            }
        )

    data = {
        "ref_range": ref_range,
        "summary": summary,
        "files": [{"path": p, "changes": c} for p, c in files.items()],
    }
    return json.dumps(data, indent=2)


def format_dry_run(info: DryRunInfo) -> str:
    lines = [
        "# semantic-git-diff --dry-run",
        f"  Refs: {info.ref_range}",
        f"  Files: {info.num_files}",
        f"  Chunks: {info.num_chunks}",
        f"  Estimated tokens: {info.estimated_tokens}",
        "",
        "## Chunks",
    ]
    for i, chunk in enumerate(info.chunks, 1):
        lines.append(f"  {i}. {chunk.filepath}")
        if chunk.function_name:
            lines.append(f"     Region: {chunk.function_name}")
        lines.append(f"     Old: {len(chunk.old_code)} chars")
        lines.append(f"     New: {len(chunk.new_code)} chars")
    lines.append("")
    lines.append("## Prompt")
    lines.append("```")
    lines.append(info.prompt)
    lines.append("```")
    return "\n".join(lines)
