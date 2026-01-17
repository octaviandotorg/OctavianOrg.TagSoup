from pydantic import BaseModel
from typing import Literal

class SuccessResponse(BaseModel):
    """Success API Response"""
    success: Literal[True] = True
    data: dict | list | str | int | None = None
