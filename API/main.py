"""FastAPI application factory for the EDMS HTTP interface."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from API.routers import auth, catalog, inventory, logistics, procurement, reporting, sales
from authentication.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
    UsernameAlreadyExistsError,
)
from shared.database import Database
from shared.error_handling import CategoryAlreadyExistsError, SpecificationAlreadyExistsError

ERROR_STATUS_CODES: dict[type[Exception], int] = {
    InvalidCredentialsError: 401,
    InvalidTokenError: 401,
    InactiveUserError: 403,
    PermissionDeniedError: 403,
    UsernameAlreadyExistsError: 409,
    CategoryAlreadyExistsError: 409,
    SpecificationAlreadyExistsError: 409,
    ValueError: 400,
    TypeError: 400,
}


def _error_handler(status_code: int):
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
        return JSONResponse(
            status_code=status_code,
            content={"detail": str(exc)},
            headers=headers,
        )

    return handler


def create_app(database_url: str = "sqlite:///edms.db") -> FastAPI:
    """Build the application, creating the schema for the configured database."""
    database = Database(database_url)
    database.create_schema()

    app = FastAPI(title="EDMS API", version="1.0.0")
    app.state.database = database

    for error_type, status_code in ERROR_STATUS_CODES.items():
        app.add_exception_handler(error_type, _error_handler(status_code))

    for module in (auth, catalog, inventory, sales, procurement, logistics, reporting):
        app.include_router(module.router, prefix="/api")

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
