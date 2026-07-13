from __future__ import annotations

import typer
import uvicorn

from serving.config import ServingSettings

cli = typer.Typer(add_completion=False, no_args_is_help=True)


@cli.command()
def run(
    host: str | None = typer.Option(None, help="Bind host"),
    port: int | None = typer.Option(None, help="Bind port"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
) -> None:
    settings = ServingSettings.from_yaml()
    uvicorn.run(
        "serving.app:app",
        host=host or settings.host,
        port=port or settings.port,
        reload=reload,
    )


if __name__ == "__main__":
    cli()
