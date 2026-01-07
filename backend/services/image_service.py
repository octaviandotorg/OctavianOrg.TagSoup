import hashlib
import tempfile
import shutil
from pathlib import Path

from fastapi import UploadFile, HTTPException
from models import ImageInfo
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
                    tags=['untagged',]
                )

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
