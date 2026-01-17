from pydantic import BaseModel
from typing import Literal

class ErrorResponse(BaseModel):
    """Error API Response"""
    success: Literal[False] = False
    code: int
    message: str
    error_type: str
    details: dict | None = None
