from __future__ import annotations

from pathlib import Path

import typer

from ingest.batch.pipeline import run_batch_pipeline, run_reprocess_from_trigger
from ingest.config import IngestSettings
from ingest.online.infer_publish import publish_infer_features
from ingest.online.validator import validate_scenario_file

app = typer.Typer(help="GIFI Ingest Engine CLI")


@app.command("batch")
def batch(
    source: Path = typer.Argument(..., help="Excel/CSV histórico QM×Processo"),
) -> None:
    settings = IngestSettings.from_yaml()
    result = run_batch_pipeline(source, settings)
    typer.echo(result)


@app.command("scenario-validate")
def scenario_validate(
    file: Path = typer.Argument(..., help="CSV/XLSX de cenário"),
    cenario_id: str = typer.Option(..., "--cenario-id"),
) -> None:
    result = validate_scenario_file(file, cenario_id)
    typer.echo(result)


@app.command("scenario-publish")
def scenario_publish(
    file: Path = typer.Argument(..., help="CSV/XLSX de cenário válido"),
    cenario_id: str = typer.Option(..., "--cenario-id"),
) -> None:
    path = publish_infer_features(file, cenario_id)
    typer.echo({"infer_features": str(path)})


@app.command("reprocess")
def reprocess(
    trigger: str = typer.Option("accept-reject", "--trigger"),
) -> None:
    if trigger != "accept-reject":
        raise typer.BadParameter("only accept-reject trigger supported in MVP")
    result = run_reprocess_from_trigger()
    typer.echo(result)


if __name__ == "__main__":
    app()
