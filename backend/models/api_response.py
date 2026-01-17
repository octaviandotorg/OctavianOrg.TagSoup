from typing import Union
from .success_response import SuccessResponse
from .error_response import ErrorResponse

ApiResponse = Union[SuccessResponse, ErrorResponse]
