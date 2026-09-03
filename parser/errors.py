"""Exceptions raised while parsing map files."""


class ParseError(Exception):
    """Represent a map-format error with an optional source line."""

    def __init__(self, message: str, line_no: int | None = None) -> None:
        """Initialize the error message and optional line number."""
        self.message = message
        self.line_no = line_no
        super().__init__(message)

    def __str__(self) -> str:
        """Return the error in the format shown to the user."""
        if self.line_no is None:
            return self.message
        return f"Error on line {self.line_no}: {self.message}"
