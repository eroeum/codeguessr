"""Views."""
from flask import Blueprint, send_from_directory, Response

blp = Blueprint("app", __file__)

@blp.route("/", methods=["GET"])
def index() -> Response:
    """Frontend"""
    return send_from_directory("./", "./public/browser/index.html")

@blp.route("/<path:path>", methods=["GET"])
def static_path(path: str) -> Response:
    """Static frontend paths."""
    return send_from_directory("./", f"./public/browser/{path}")
