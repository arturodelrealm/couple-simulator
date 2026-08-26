class AppError(Exception):
    """Domain or application error mapped to a structured API error response."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        field: str | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field = field
        super().__init__(message)
