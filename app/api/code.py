"""Provides endpoints for code data."""
import os
import pathlib

from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.api.models.code_schema import FileSchema
from app.utils.files import get_files

blp = Blueprint(
    "Code",
    "code",
    url_prefix="/api/v1/code",
    description="Operations on file data."
)

@blp.route("/")
class Files(MethodView):
    """Provides files in the watched directory."""

    @staticmethod
    @blp.response(200, FileSchema(many=True))
    def get() -> list[dict]:
        """Provides list of files."""
        with current_app.app_context():
            code_path = current_app.config["CODE_PATH"]
        files = get_files(code_path)
        resp = [
            {
                "path": os.path.dirname(os.path.relpath(path, code_path)),
                "file_name": os.path.basename(path),
                "file_type": pathlib.Path(path).suffix,
            }
            for path in files
            if not os.path.relpath(path, code_path).startswith(".git" + os.path.sep)
        ]
        return resp


@blp.route("/<path:path>")
class FileContent(MethodView):
    """Provide file contents."""

    @staticmethod
    def get(path: str) -> dict:
        """Gets file contents."""
        with current_app.app_context():
            code_path = current_app.config["CODE_PATH"]

        file_path = os.path.join(code_path, path)
        if not os.path.isfile(file_path):
            abort(404, message="Unable to find file")

        with open(file_path, "r", encoding="utf-8") as fd:
            contents = fd.read()

        return {
            "path": os.path.dirname(os.path.relpath(file_path, code_path)),
            "file_name": os.path.basename(file_path),
            "file_type": pathlib.Path(file_path).suffix,
            "contents": contents
        }
