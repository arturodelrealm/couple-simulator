from gettext import gettext as _

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.shared.exceptions import AppError

DEFAULT_ERROR_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_ERROR",
}


def _error_payload(
    code: str,
    message: str,
    *,
    field: str | None = None,
) -> dict[str, list[dict[str, str | None]]]:
    error: dict[str, str | None] = {"code": code, "message": message}
    if field is not None:
        error["field"] = field
    return {"errors": [error]}


def _validation_field(location: tuple[str | int, ...]) -> str | None:
    if not location:
        return None
    return ".".join(str(part) for part in location)


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.code, exc.message, field=exc.field),
    )


async def http_exception_handler(
    _request: Request,
    exc: HTTPException,
) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "errors" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)

    if isinstance(detail, list):
        errors = []
        for item in detail:
            if isinstance(item, dict) and "code" in item and "message" in item:
                errors.append(item)
            else:
                errors.append(
                    {
                        "code": DEFAULT_ERROR_CODES.get(
                            exc.status_code,
                            "HTTP_ERROR",
                        ),
                        "message": str(item),
                    }
                )
        return JSONResponse(status_code=exc.status_code, content={"errors": errors})

    code = DEFAULT_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
    message = str(detail) if detail else _("Request failed")
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(code, message),
    )


async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "code": "VALIDATION_ERROR",
                "message": error.get("msg", _("Validation error")),
                "field": _validation_field(error.get("loc", ())),
            }
        )
    return JSONResponse(status_code=422, content={"errors": errors})


async def unhandled_exception_handler(
    _request: Request,
    _exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_error_payload("INTERNAL_ERROR", _("Internal server error")),
    )
