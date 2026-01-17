import hashlib
import tempfile
import shutil
from pathlib import Path

from fastapi import UploadFile, HTTPException
from PIL import Image, ImageOps

from models import ImageInfo, PaginatedImagesResponse
from repositories import ImageRepository

# Allowed image MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/heic",
    "image/heif",
    "image/tiff",
    "image/bmp",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
THUMBNAIL_DIR = Path(__file__).parent.parent / "thumbnails"
THUMBNAIL_SIZE = 300  # 300x300 fixed area


class ImageService:
    """Service for handling image upload and retrieval operations."""

    def __init__(self, repository: ImageRepository):
        """Initialize service with repository dependency."""
        self.repository = repository

    async def upload_image(self, file: UploadFile) -> ImageInfo:
        """
        Upload an image file.

        Validates MIME type, streams file to disk with SHA1 hashing,
        and saves metadata to database.

        Args:
            file: Uploaded file from request

        Returns:
            ImageInfo with uploaded image metadata

        Raises:
            HTTPException: For validation or processing errors
        """
        # Validate MIME type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file.content_type}' is not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}",
            )

        # Stream file and calculate SHA1
        sha1_hash = hashlib.sha1()
        file_size = 0
        tmp_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

                # Stream file and calculate SHA1
                while True:
                    chunk = await file.read(8192)  # Read in 8KB chunks
                    if not chunk:
                        break

                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE:
                        tmp_file.close()  # Close file before deleting
                        tmp_path.unlink()
                        raise HTTPException(
                            status_code=413,
                            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024):.0f} MB",
                        )

                    sha1_hash.update(chunk)
                    tmp_file.write(chunk)

            # Move temp file to final location with SHA1 as filename
            image_id = sha1_hash.hexdigest()
            final_path = UPLOAD_DIR / image_id

            # Only move if file doesn't already exist (deduplication)
            if not final_path.exists():
                shutil.move(str(tmp_path), str(final_path))

            # Save metadata to database (only if not already saved)
            if not self.repository.image_exists(image_id):
                self.repository.save_image(
                    image_id=image_id,
                    mime_type=file.content_type,
                    file_size=file_size,
                    original_filename=file.filename,
                    tags=[]
                )

                # Generate thumbnail (only for new images)
                self._generate_thumbnail(image_id)

            # Return image info
            return ImageInfo(
                id=image_id,
                mime_type=file.content_type,
                file_size=file_size,
                original_filename=file.filename,
                tags=[]
            )

        except HTTPException:
            raise
        except Exception as e:
            # Clean up temp file if it still exists
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()
            raise HTTPException(status_code=500, detail=str(e))

    def _generate_thumbnail(self, image_id: str) -> None:
        """
        Generate a WebP thumbnail for the uploaded image.

        Creates a 300x300 thumbnail that preserves aspect ratio.

        Args:
            image_id: SHA1 hash of the image (used as filename)
        """
        try:
            # Ensure thumbnail directory exists
            THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

            # Open the original image
            image_path = UPLOAD_DIR / image_id
            with Image.open(image_path) as img:
                # Apply EXIF orientation (rotate if needed)
                img = ImageOps.exif_transpose(img)

                # Convert to RGB if necessary (for RGBA, GIF, etc.)
                if img.mode in ("RGBA", "LA", "P"):
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = rgb_img

                # Calculate thumbnail size to fit in 300x300 while preserving aspect ratio
                img.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.Resampling.LANCZOS)

                # Save as WebP
                thumbnail_path = THUMBNAIL_DIR / image_id
                img.save(thumbnail_path, format="WEBP", quality=80)

        except Exception as e:
            # Log error but don't fail the upload
            print(f"Warning: Failed to generate thumbnail for {image_id}: {str(e)}")

    def get_image_info(self, image_id: str) -> ImageInfo:
        """
        Get image information by ID.

        Args:
            image_id: SHA1 hash of the image

        Returns:
            ImageInfo with image metadata

        Raises:
            HTTPException: If image not found
        """
        image_data = self.repository.get_image_info(image_id)

        if not image_data:
            raise HTTPException(status_code=404, detail="Image not found")

        return ImageInfo(
            id=image_data.id,
            mime_type=image_data.mime_type,
            file_size=image_data.file_size,
            original_filename=image_data.original_filename,
            tags=image_data.tags
        )

    def get_images_info(
        self,
        page_size: int,
        tags: list[str] | None = None,
        cursor: str | None = None,
    ) -> PaginatedImagesResponse:
        """
        Get images filtered by tags with cursor-based pagination.

        Args:
            tags: Optional list of tags to filter by (e.g., ['untagged'], ['vacation', 'beach']).
                  Images must have ALL tags (AND logic).
            page_size: Number of items per page (1-100)
            cursor: Cursor from previous page, or None for first page

        Returns:
            PaginatedImagesResponse with items, next_cursor, and metadata

        Raises:
            HTTPException: For invalid page_size
        """
        # Validate page_size
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=400,
                detail="page_size must be between 1 and 100",
            )

        # Normalize tags and cursor
        normalized_tags = tags if tags else None
        normalized_cursor = None if not cursor else cursor

        # Request page_size + 1 to determine if there are more results
        items = self.repository.get_images_by_tag(
            limit=page_size + 1,
            tags=normalized_tags,
            cursor=normalized_cursor,
        )

        # Determine if there are more results and extract next cursor
        has_more = len(items) > page_size
        next_cursor = None

        if has_more:
            next_cursor = items[page_size - 1].original_filename
            items = items[:page_size]

        return PaginatedImagesResponse(
            items=items,
            next_cursor=next_cursor,
            page_size=page_size,
            has_more=has_more,
        )

    def add_image_tag(
        self,
        image_id: str,
        tag: str
    ) -> None:
        """
        Adds a tag to an image.

        Args:
            image_id: The image id.
            tag: The tag.

        Returns:
            Ok
        """
        self.repository.add_image_tag(image_id, tag)

    def delete_image_tag(
        self,
        image_id: str,
        tag: str
    ) -> None:
        """
        Deletes a tag from an image.

        Args:
            image_id: The image id.
            tag: The tag.

        Returns:
            Ok
        """
        self.repository.delete_image_tag(image_id, tag)

    def get_image_tags(
        self
    ) -> List[str]:
        """
        Gets all image tags.

        Returns:
            List of image tags.
        """
        return self.repository.get_image_tags()
