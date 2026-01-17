from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Response, Depends, Query, HTTPException
from fastapi.responses import FileResponse

from models import ImageInfo, PaginatedImagesResponse, SuccessResponse, ErrorResponse
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
) -> SuccessResponse | ErrorResponse:
    """
    Upload a new image.

    Accepts image files, streams them to disk with SHA1 hashing,
    and stores metadata in the database.

    Returns:
        201 Created with SuccessResponse containing ImageInfo
    """
    try:
        image_info = await service.upload_image(file)
        return SuccessResponse(data=image_info.model_dump())
    except HTTPException as e:
        return ErrorResponse(
            code=e.status_code,
            message=e.detail if isinstance(e.detail, str) else str(e.detail),
            error_type="UPLOAD_ERROR",
        )


@router.post("/{image_id}/addImageTag/{tag}", status_code=200)
async def add_image_tag(
    image_id: str,
    tag: str,
    service: ImageService = Depends(get_image_service),
) -> SuccessResponse | ErrorResponse:
    """
    Add a tag to an image.

    Returns:
        200 Ok with SuccessResponse
    """
    try:
        service.add_image_tag(image_id, tag)
        return SuccessResponse()
    except HTTPException as e:
        return ErrorResponse(
            code=e.status_code,
            message=e.detail if isinstance(e.detail, str) else str(e.detail),
            error_type="TAG_ERROR",
        )

@router.post("/{image_id}/deleteImageTag/{tag}", status_code=200)
async def delete_image_tag(
    image_id: str,
    tag: str,
    service: ImageService = Depends(get_image_service),
) -> SuccessResponse | ErrorResponse:
    """
    Deletes a tag from an image.

    Returns:
        200 Ok with SuccessResponse
    """
    try:
        service.delete_image_tag(image_id, tag)
        return SuccessResponse()
    except HTTPException as e:
        return ErrorResponse(
            code=e.status_code,
            message=e.detail if isinstance(e.detail, str) else str(e.detail),
            error_type="TAG_ERROR",
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


@router.get("/getImageInfo/{image_id}", response_model=SuccessResponse | ErrorResponse)
async def get_image_info(
    image_id: str,
    service: ImageService = Depends(get_image_service),
) -> SuccessResponse | ErrorResponse:
    """
    Get image metadata by ID.

    Args:
        image_id: SHA1 hash of the image

    Returns:
        SuccessResponse with ImageInfo data
    """
    try:
        image_info = service.get_image_info(image_id)
        return SuccessResponse(data=image_info.model_dump())
    except HTTPException as e:
        return ErrorResponse(
            code=e.status_code,
            message=e.detail if isinstance(e.detail, str) else str(e.detail),
            error_type="NOT_FOUND",
        )


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


@router.get("/getImagesInfo", response_model=SuccessResponse | ErrorResponse)
async def get_images_info(
    tag: list[str] | None = Query(None, description="Tags to filter images by. Images must have ALL tags. Can be specified multiple times: ?tag=vacation&tag=beach"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    cursor: str | None = Query(None, description="Cursor for next page"),
    service: ImageService = Depends(get_image_service),
) -> SuccessResponse | ErrorResponse:
    """
    Get images filtered by tags with cursor-based pagination.

    Args:
        tag: Tags to filter by (e.g., 'untagged', 'vacation', 'beach').
             Can specify multiple times to filter by multiple tags.
             Images must have ALL specified tags (AND logic).
        page_size: Number of items per page (1-100, default 20)
        cursor: Cursor from previous page for pagination, or None for first page

    Returns:
        SuccessResponse with PaginatedImagesResponse data
    """
    try:
        paginated_response = service.get_images_info(tags=tag, page_size=page_size, cursor=cursor)
        return SuccessResponse(data=paginated_response.model_dump())
    except HTTPException as e:
        return ErrorResponse(
            code=e.status_code,
            message=e.detail if isinstance(e.detail, str) else str(e.detail),
            error_type="QUERY_ERROR",
        )

@router.get("/getImageTags", response_model=SuccessResponse | ErrorResponse)
async def get_image_tags(
    service: ImageService = Depends(get_image_service),
) -> SuccessResponse | ErrorResponse:
    """
    Gets all image tags in the database.

    Returns:
        SuccessResponse with list of string tags.
    """
    try:
        tags = service.get_image_tags()
        return SuccessResponse(data=tags)
    except HTTPException as e:
        return ErrorResponse(
            code=e.status_code,
            message=e.detail if isinstance(e.detail, str) else str(e.detail),
            error_type="QUERY_ERROR",
        )
