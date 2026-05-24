import subprocess
from typing import Optional

import unidiff


def run_git_diff(ref_range: str) -> str:
    args = ["git", "diff"]
    args.extend(ref_range.split())
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        msg = result.stderr.strip() or "git diff failed (not a git repo? invalid refs?)"
        raise RuntimeError(msg)
    return result.stdout


def parse_diff_text(diff_text: str) -> unidiff.PatchSet:
    return unidiff.PatchSet(diff_text)
