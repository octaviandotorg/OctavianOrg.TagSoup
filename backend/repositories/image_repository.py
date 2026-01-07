from db import get_db_connection
from models import ImageInfo


class ImageRepository:
    """Repository for image database operations."""

    def save_image(
        self,
        image_id: str,
        mime_type: str,
        file_size: int,
        original_filename: str,
        tags: list[str],
    ) -> None:
        """
        Save image metadata to the database.

        Args:
            image_id: SHA1 hash of the image file
            mime_type: MIME type of the image (e.g., 'image/jpeg')
            file_size: Size of the image file in bytes
            original_filename: Original filename as uploaded
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # insert into images table
        cursor.execute(
            '''
            INSERT INTO images (image_id, mime_type, file_size, original_file_name)
            VALUES (?, ?, ?, ?)
            ''',
            (image_id, mime_type, file_size, original_filename),
        )

        # insert into tags table
        for tag in tags:
            cursor.execute(
                '''
                INSERT INTO tags (image_id, tag)
                VALUES (?, ?)
                ''',
                (image_id, tag),
            )

        conn.commit()
        conn.close()

    def get_image_info(self, image_id: str) -> dict | None:
        """
        Get image metadata by ID.

        Args:
            image_id: SHA1 hash of the image

        Returns:
            Image metadata dict or None if not found
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT image_id, mime_type, file_size, original_file_name
            FROM images
            WHERE image_id = ?
            ''',
            (image_id,),
        )

        row = cursor.fetchone()

        if row:
            result = ImageInfo(id=row[0], mime_type=row[1], file_size=row[2], original_filename=row[3], tags=[])
            cursor.execute(
                '''
                SELECT tag
                FROM tags
                WHERE image_id = ?
                ''',
                (image_id,),
            )

            rows = cursor.fetchall()

            for tag_row in rows:
                result.tags.append(tag_row[0])

            conn.close()
            return result

        conn.close()
        return None

    def image_exists(self, image_id: str) -> bool:
        """Check if an image exists in the database."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT 1 FROM images WHERE image_id = ?', (image_id,))
        exists = cursor.fetchone() is not None
        conn.close()

        return exists
