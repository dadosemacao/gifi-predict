from __future__ import annotations

from pathlib import Path

import typer

from simulation.config import SimulationSettings
from simulation.pipeline.evaluate import run_evaluate_pipeline
from simulation.pipeline.infer import run_infer_pipeline
from simulation.pipeline.train import run_train_pipeline

app = typer.Typer(help="GIFI Simulation Engine CLI")


@app.command("train")
def train(
    l2_root: Path | None = typer.Option(None, "--l2-root", help="Override L2 root"),
) -> None:
    settings = SimulationSettings.from_yaml()
    if l2_root is not None:
        settings = settings.model_copy(update={"l2_root": l2_root})
    result = run_train_pipeline(settings)
    typer.echo(result)


@app.command("evaluate")
def evaluate(
    run_id: str | None = typer.Option(None, "--run-id"),
    l2_root: Path | None = typer.Option(None, "--l2-root"),
) -> None:
    settings = SimulationSettings.from_yaml()
    if l2_root is not None:
        settings = settings.model_copy(update={"l2_root": l2_root})
    result = run_evaluate_pipeline(settings, run_id=run_id)
    typer.echo(result)


@app.command("infer")
def infer(
    cenario_id: str = typer.Option(..., "--cenario-id"),
    mode: str = typer.Option("A", "--mode", help="A or B"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    settings = SimulationSettings.from_yaml()
    result = run_infer_pipeline(
        settings,
        cenario_id=cenario_id,
        mode=mode,
        output=output,
    )
    typer.echo(result)


if __name__ == "__main__":
    app()
