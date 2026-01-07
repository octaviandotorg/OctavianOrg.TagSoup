from pydantic import BaseModel

class ImageInfo(BaseModel):
    """Image metadata information"""
    id: str
    mime_type: str
    file_size: int
    original_filename: str
    tags: list[str]
