from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None


def success_response(data: Any) -> dict:
    return {"success": True, "data": data, "error": None}


def error_response(message: str, status_code: int = 400) -> dict:
    return {"success": False, "data": None, "error": message}
