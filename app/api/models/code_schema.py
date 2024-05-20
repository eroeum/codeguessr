"""Schema for code info."""
import marshmallow as ma


class FileSchema(ma.Schema):
    """Data definition for file representation."""

    file_name = ma.fields.Str(required=True)
    """Defines the name of the file."""

    path = ma.fields.Str(required=True)
    """Defines the path for the file."""

    file_type = ma.fields.Str(required=True)
    """File Type (extension)."""


class FileContentSchema(FileSchema):
    """Data definition for detailed view."""
    contents = ma.fields.Str(required=True)
