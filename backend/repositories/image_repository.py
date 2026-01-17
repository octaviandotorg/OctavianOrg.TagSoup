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

    def get_images_by_tag(
        self,
        limit: int,
        tags: list[str] | None = None,
        cursor: str | None = None,
    ) -> list[ImageInfo]:
        """
        Get images filtered by tags with cursor-based pagination.

        Args:
            tags: Optional list of tags to filter by (e.g., ['vacation', 'beach']).
                  Images must have ALL tags (AND logic).
            limit: Maximum number of results to return
            cursor: Last image_id from previous page, or None for first page

        Returns:
            List of ImageInfo objects ordered by image_id
        """
        conn = get_db_connection()
        db_cursor = conn.cursor()

        # Build query with cursor and tag support
        if tags and len(tags) > 0:
            # Filter by multiple tags (AND logic) - image must have all tags
            placeholders = ','.join('?' * len(tags))
            cursor_condition = 'AND i2.original_file_name > ?' if cursor else ''

            query = f'''
                SELECT i.image_id, i.mime_type, i.file_size, i.original_file_name, t.tag
                FROM images i
                LEFT JOIN tags t ON i.image_id = t.image_id
                WHERE i.image_id IN (
                    SELECT i2.image_id
                    FROM images i2
                    WHERE EXISTS (
                        SELECT 1 FROM tags t2
                        WHERE t2.image_id = i2.image_id AND t2.tag IN ({placeholders})
                        GROUP BY t2.image_id
                        HAVING COUNT(DISTINCT t2.tag) = {len(tags)}
                    )
                    {cursor_condition}
                    ORDER BY i2.original_file_name
                    LIMIT ?
                )
                ORDER BY i.original_file_name, t.tag
            '''

            params = tags + ([cursor] if cursor else []) + [limit]
            db_cursor.execute(query, params)
        else:
            # No tag filter - return all images
            if cursor:
                query = '''
                    SELECT i.image_id, i.mime_type, i.file_size, i.original_file_name, t.tag
                    FROM images i
                    LEFT JOIN tags t ON i.image_id = t.image_id
                    WHERE i.image_id IN (
                        SELECT image_id
                        FROM images
                        WHERE original_file_name > ?
                        ORDER BY original_file_name
                        LIMIT ?
                    )
                    ORDER BY i.original_file_name, t.tag
                '''
                db_cursor.execute(query, (cursor, limit))
            else:
                query = '''
                    SELECT i.image_id, i.mime_type, i.file_size, i.original_file_name, t.tag
                    FROM images i
                    LEFT JOIN tags t ON i.image_id = t.image_id
                    WHERE i.image_id IN (
                        SELECT image_id
                        FROM images
                        ORDER BY original_file_name
                        LIMIT ?
                    )
                    ORDER BY i.original_file_name, t.tag
                '''
                db_cursor.execute(query, (limit,))

        rows = db_cursor.fetchall()
        conn.close()

        # Build ImageInfo objects from result set
        # Results may have multiple rows per image (one per tag)
        results = {}
        for row in rows:
            image_id = row[0]
            if image_id not in results:
                results[image_id] = ImageInfo(
                    id=image_id,
                    mime_type=row[1],
                    file_size=row[2],
                    original_filename=row[3],
                    tags=[]
                )
            if row[4]:  # tag is not null
                results[image_id].tags.append(row[4])

        return list(results.values())

    def add_image_tag(
        self,
        image_id: str,
        tag: str
    ) -> None:
        conn = get_db_connection()
        db_cursor = conn.cursor()

        db_cursor.execute(
            '''
            INSERT INTO tags (image_id, tag)
            VALUES (?, ?)
            ON CONFLICT DO NOTHING
            ''',
            (image_id, tag)
        )

        conn.commit()
        conn.close()

    def delete_image_tag(
        self,
        image_id: str,
        tag: str
    ) -> None:
        conn = get_db_connection()
        db_cursor = conn.cursor()

        db_cursor.execute(
            '''
            DELETE FROM tags
            WHERE image_id = ? AND tag = ?
            ''',
            (image_id, tag)
        )

        conn.commit()
        conn.close()

    def get_image_tags(
        self,
    ) -> List[str]:
        conn = get_db_connection()
        db_cursor = conn.cursor()

        db_cursor.execute(
            '''
            SELECT DISTINCT tag
            FROM tags
            '''
        )

        rows = db_cursor.fetchall()
        results = [row[0] for row in rows]
        conn.close()
        return results;
