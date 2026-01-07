from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Response, Depends, Query
from fastapi.responses import FileResponse

from models import ImageInfo, PaginatedImagesResponse
from services import ImageService
from repositories import ImageRepository
from services.image_service import UPLOAD_DIR, THUMBNAIL_DIR

router = APIRouter(prefix="/api/image", tags=["images"])


def get_image_service() -> ImageService:
    """Dependency injection for ImageService."""
    repository = ImageRepository()
    return ImageService(repository)


@router.post("/uploadImage", status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    service: ImageService = Depends(get_image_service),
) -> Response:
    """
    Upload a new image.

    Accepts image files, streams them to disk with SHA1 hashing,
    and stores metadata in the database.

    Returns:
        201 Created with ImageInfo JSON and Location header
    """
    image_info = await service.upload_image(file)

    return Response(
        content=image_info.model_dump_json(),
        status_code=201,
        headers={"Location": f"/api/image/getImageInfo/{image_info.id}"},
        media_type="application/json",
    )


@router.get("/getImage/{image_id}")
async def get_image(
    image_id: str,
    service: ImageService = Depends(get_image_service),
) -> FileResponse:
    """
    Get image file by ID.

    Args:
        image_id: SHA1 hash of the image

    Returns:
        Image file content with appropriate Content-Type and Content-Disposition headers
    """
    # Get image metadata from database (validates image exists, returns 404 if not)
    image_info = service.get_image_info(image_id)

    # Construct file path
    file_path = UPLOAD_DIR / image_id

    # Return file with appropriate headers
    return FileResponse(
        path=file_path,
        media_type=image_info.mime_type,
        filename=image_info.original_filename,
        headers={"Content-Disposition": f"inline; filename={image_info.original_filename}"},
    )


@router.get("/getImageInfo/{image_id}", response_model=ImageInfo)
async def get_image_info(
    image_id: str,
    service: ImageService = Depends(get_image_service),
) -> ImageInfo:
    """
    Get image metadata by ID.

    Args:
        image_id: SHA1 hash of the image

    Returns:
        ImageInfo with image metadata
    """
    return service.get_image_info(image_id)


@router.get("/getImageThumbnail/{image_id}")
async def get_image_thumbnail(
    image_id: str,
    service: ImageService = Depends(get_image_service),
) -> FileResponse:
    """
    Get image thumbnail by ID.

    Args:
        image_id: SHA1 hash of the image

    Returns:
        Thumbnail image file in WebP format
    """
    # Get image metadata from database (validates image exists, returns 404 if not)
    image_info = service.get_image_info(image_id)

    # Construct thumbnail file path
    thumbnail_path = THUMBNAIL_DIR / image_id

    # Return thumbnail file
    return FileResponse(
        path=thumbnail_path,
        media_type="image/webp",
        filename=f"{Path(image_info.original_filename).stem}_thumb.webp",
        headers={"Content-Disposition": f"inline; filename={Path(image_info.original_filename).stem}_thumb.webp"},
    )


@router.get("/getImagesInfo", response_model=PaginatedImagesResponse)
async def get_images_info(
    tag: str = Query(..., description="Tag to filter images by"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    cursor: str | None = Query(None, description="Cursor for next page"),
    service: ImageService = Depends(get_image_service),
) -> PaginatedImagesResponse:
    """
    Get images filtered by tag with cursor-based pagination.

    Args:
        tag: Tag to filter by (e.g., 'untagged', 'vacation')
        page_size: Number of items per page (1-100, default 20)
        cursor: Cursor from previous page for pagination, or None for first page

    Returns:
        PaginatedImagesResponse with items, next_cursor, and metadata
    """
    return service.get_images_info(tag=tag, page_size=page_size, cursor=cursor)
