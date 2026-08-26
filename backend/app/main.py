from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.schemas.responses import ok
from app.shared.exception_handlers import (
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.shared.exceptions import AppError

app = FastAPI(title="Couple Life Simulator API")

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
api_router = APIRouter()
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
def health_check() -> dict[str, object]:
    return ok({"status": "ok"})
