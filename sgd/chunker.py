import re
from typing import List, Tuple

import unidiff

from sgd.models import Chunk

FUNC_PATTERNS = [
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+\w+"),
    re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s+\w+"),
    re.compile(r"^\s*(?:async\s+)?def\s+\w+"),
    re.compile(r"^\s*class\s+\w+"),
    re.compile(r"^\s*(?:public|private|protected)\s+(?:static\s+)?(?:async\s+)?function\s+\w+"),
    re.compile(r"^\s*(?:public|private|protected)\s+(?:static\s+)?\w+\s+\w+\s*\("),
    re.compile(r"^\s*fn\s+\w+"),
    re.compile(r"^\s*func\s+\w+"),
    re.compile(r"^\s*def\s+\w+"),
    re.compile(r"^\s*(?:const|let|var)\s+\w+\s*=\s*(?:\([^)]*\)|\w+)\s*=>"),
    re.compile(r"^\s*(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?function"),
]


def _get_lt(lt):
    if not isinstance(lt, str):
        return lt.value
    return lt


def detect_function_name(line: str) -> str | None:
    for pattern in FUNC_PATTERNS:
        m = pattern.search(line.strip())
        if m:
            return m.group().strip()
    return None


def _extract_old_new(lines_info: List[Tuple]) -> Tuple[str, str]:
    old_lines: list[str] = []
    new_lines: list[str] = []
    for _, lt, val in lines_info:
        if lt in (" ", "-"):
            old_lines.append(val)
        if lt in (" ", "+"):
            new_lines.append(val)
    return "\n".join(old_lines), "\n".join(new_lines)


def _merge_consecutive(chunks: List[Chunk]) -> List[Chunk]:
    merged: list[Chunk] = []
    for chunk in chunks:
        if (
            merged
            and merged[-1].filepath == chunk.filepath
            and merged[-1].function_name == chunk.function_name
        ):
            prev = merged[-1]
            old_joiner = "\n" if prev.old_code and chunk.old_code else ""
            new_joiner = "\n" if prev.new_code and chunk.new_code else ""
            merged[-1] = Chunk(
                filepath=prev.filepath,
                function_name=prev.function_name,
                old_code=prev.old_code + old_joiner + chunk.old_code,
                new_code=prev.new_code + new_joiner + chunk.new_code,
            )
        else:
            merged.append(chunk)
    return merged


def chunk_patched_file(pf: unidiff.PatchedFile) -> List[Chunk]:
    raw_chunks: list[Chunk] = []
    for hunk in pf:
        lines = list(hunk)
        if not lines:
            continue

        line_info = [
            (line, _get_lt(line.line_type), line.value.rstrip("\n"))
            for line in lines
        ]

        boundaries: List[Tuple[int, str]] = []
        for i, (_, lt, val) in enumerate(line_info):
            name = detect_function_name(val)
            if name:
                boundaries.append((i, name))

        if not boundaries:
            old_code, new_code = _extract_old_new(line_info)
            if not old_code and not new_code:
                continue
            func_name = ""
            if hunk.section_header:
                func_name = hunk.section_header.strip()
            raw_chunks.append(Chunk(filepath=pf.path, function_name=func_name, old_code=old_code, new_code=new_code))
        else:
            for j, (boundary_idx, func_name) in enumerate(boundaries):
                next_idx = boundaries[j + 1][0] if j + 1 < len(boundaries) else len(lines)
                segment = line_info[boundary_idx:next_idx]
                old_code, new_code = _extract_old_new(segment)
                if not old_code and not new_code:
                    continue
                raw_chunks.append(Chunk(filepath=pf.path, function_name=func_name, old_code=old_code, new_code=new_code))

    return _merge_consecutive(raw_chunks)


def chunk_diff(patch_set: unidiff.PatchSet) -> List[Chunk]:
    chunks: list[Chunk] = []
    for pf in patch_set:
        chunks.extend(chunk_patched_file(pf))
    return chunks
