from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown

from sgd import __version__
from sgd.chunker import chunk_diff
from sgd.formatter import format_dry_run, format_json, format_markdown
from sgd.llm import query_llm
from sgd.models import DryRunInfo
from sgd.parser import parse_diff_text, run_git_diff
from sgd.prompt import build_prompt, estimate_tokens

console = Console()

def _version_callback(show: bool) -> None:
    if show:
        console.print(f"sgd v{__version__}")
        raise typer.Exit()

app = typer.Typer(
    name="sgd",
    help="semantic-git-diff — summarize git diffs in plain English using a local LLM",
)


@app.command()
def main(
    refs: str = typer.Argument(
        ...,
        help="Git ref range (e.g. main..feature or HEAD~3 HEAD)",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Write output to file instead of stdout"
    ),
    model: str = typer.Option(
        "qwen2.5:3b", "--model", "-m", help="Ollama model name"
    ),
    lang: str = typer.Option(
        "en", "--lang", "-l", help="Output language"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show prompt and chunk info without calling LLM"
    ),
    output_format: str = typer.Option(
        "markdown", "--format", "-f", help="Output format: markdown or json"
    ),
    max_chunks: int = typer.Option(
        50, "--max-chunks", help="Maximum number of chunks to process"
    ),
    version: bool = typer.Option(
        False, "--version", help="Show version and exit",
        callback=_version_callback, is_eager=True,
    ),
):
    with console.status(f"Running git diff {refs}..."):
        try:
            diff_text = run_git_diff(refs)
        except RuntimeError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(code=1)

    if not diff_text.strip():
        console.print("[yellow]No diff output — refs may be identical or invalid.[/yellow]")
        raise typer.Exit()

    patch_set = parse_diff_text(diff_text)
    chunks = chunk_diff(patch_set)

    if not chunks:
        console.print("[yellow]No changes detected after parsing.[/yellow]")
        raise typer.Exit()

    if len(chunks) > max_chunks:
        console.print(
            f"[yellow]Warning: {len(chunks)} chunks exceeds --max-chunks={max_chunks}. "
            f"Truncating to {max_chunks}.[/yellow]"
        )
        chunks = chunks[:max_chunks]

    prompt = build_prompt(chunks, lang=lang)
    total_tokens = estimate_tokens(prompt)
    if total_tokens > 24000:
        console.print(
            f"[yellow]Warning: ~{total_tokens} estimated tokens exceeds 24k limit. "
            f"Truncating chunks.[/yellow]"
        )
        while chunks and estimate_tokens(build_prompt(chunks, lang=lang)) > 24000:
            chunks.pop()

    if dry_run:
        info = DryRunInfo(
            ref_range=refs,
            num_files=len({c.filepath for c in chunks}),
            num_chunks=len(chunks),
            chunks=chunks,
            prompt=prompt,
            estimated_tokens=estimate_tokens(prompt),
        )
        output_text = format_dry_run(info)
    else:
        with console.status(f"Querying {model}..."):
            try:
                summary = query_llm(prompt, model=model)
            except RuntimeError as e:
                console.print(f"[red]Error: {e}[/red]")
                raise typer.Exit(code=1)

        if output_format == "json":
            output_text = format_json(summary, chunks, refs)
        else:
            output_text = format_markdown(summary, chunks, refs)

    if output:
        with open(output, "w") as f:
            f.write(output_text)
        console.print(f"[green]Output written to {output}[/green]")
    else:
        if output_format == "json" or dry_run:
            console.print(output_text)
        else:
            md = Markdown(output_text)
            console.print(md)


if __name__ == "__main__":
    app()
