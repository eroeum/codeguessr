"""Shim to provide the Flask application."""
import argparse

from app import app

create_app = app.create_app

def main() -> None:
    """Entry-point to the application on CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root_dir", dest="filename", help="Provide the root path of the directory to guess.", default=None
    )

    args = parser.parse_args()
    app = create_app(args.filename)
    app.run(port=8080)
