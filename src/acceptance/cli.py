from __future__ import annotations

from pathlib import Path

import typer

from acceptance.config import AcceptanceSettings
from acceptance.pipeline.accept import run_accept_pipeline
from acceptance.pipeline.report import run_report_pipeline

app = typer.Typer(help="GIFI Acceptance Gate CLI")


@app.command("run")
def run(
    run_id: str = typer.Option(..., "--run-id"),
    l2_root: Path | None = typer.Option(None, "--l2-root"),
) -> None:
    settings = AcceptanceSettings.from_yaml()
    if l2_root is not None:
        settings = settings.model_copy(update={"l2_root": l2_root})
    result = run_accept_pipeline(settings, run_id=run_id)
    typer.echo(result)


@app.command("report")
def report(
    run_id: str = typer.Option(..., "--run-id"),
) -> None:
    settings = AcceptanceSettings.from_yaml()
    result = run_report_pipeline(settings, run_id=run_id)
    typer.echo(result)


if __name__ == "__main__":
    app()
