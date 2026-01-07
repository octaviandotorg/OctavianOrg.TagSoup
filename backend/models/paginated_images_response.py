from pydantic import BaseModel
from .image_info import ImageInfo


class PaginatedImagesResponse(BaseModel):
    """Paginated response for images filtered by tag"""
    items: list[ImageInfo]
    next_cursor: str | None
    page_size: int
    has_more: bool
