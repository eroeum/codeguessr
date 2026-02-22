"""Command-line interface for CodeGuessr.

Provides the ``codeguessr`` entry point that scans a directory, starts a
local uvicorn server, and opens the game in the default browser.
"""

import os
import threading
import time
import webbrowser
from pathlib import Path

import click
import uvicorn


def _open_browser(url: str) -> None:
    """Open *url* in the default browser after a short delay.

    The delay allows uvicorn to finish binding before the browser loads the
    page.

    Args:
        url: The URL to open.
    """
    time.sleep(1.5)
    webbrowser.open(url)


@click.command()
@click.argument("directory", default=None, required=False)
@click.option("--port", default=4200, show_default=True, help="Port to run the server on.")
def main(directory: str | None, port: int) -> None:
    """CodeGuessr — a GeoGuessr-style browser game for code.

    Scans DIRECTORY (default: current directory) for code files and starts
    a local web server with the game.
    """
    root = Path(directory).resolve() if directory else Path.cwd()

    if not root.is_dir():
        raise click.BadParameter(f"{root} is not a directory", param_hint="DIRECTORY")

    static_index = Path(__file__).parent / "static" / "browser" / "index.html"
    if not static_index.exists():
        click.echo(
            "Error: Static files not found. Please build the client first:\n\n"
            "  make build\n\n"
            "or:\n\n"
            "  cd client && npm install && npm run build"
            " -- --output-path=../src/codeguessr/static",
            err=True,
        )
        raise SystemExit(1)

    os.environ["CODEGUESSR_DIR"] = str(root)

    url = f"http://localhost:{port}"
    click.echo(f"Starting CodeGuessr for: {root}")
    click.echo(f"Opening {url} ...")

    browser_thread = threading.Thread(target=_open_browser, args=(url,), daemon=True)
    browser_thread.start()

    uvicorn.run("codeguessr.server:app", host="0.0.0.0", port=port)
