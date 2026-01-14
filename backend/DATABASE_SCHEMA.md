# TagSoup Database Schema

## Overview

The TagSoup database stores image metadata and associated tags. Images are identified by their SHA1 hash to enable deduplication. Tags are stored in a separate table to support flexible many-to-many relationships.

## Database Constraints

- **Foreign Keys**: Enabled via `PRAGMA foreign_keys = ON`
- **Cascade Deletes**: Deleting an image automatically removes all associated tags

## Tables

### images

Stores core image metadata.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `image_id` | TEXT | PRIMARY KEY | SHA1 hash of the image file (40 hex characters) |
| `mime_type` | TEXT | NOT NULL | MIME type of the image (e.g., `image/jpeg`, `image/png`) |
| `file_size` | INTEGER | NOT NULL | Size of the image file in bytes |
| `original_file_name` | TEXT | NOT NULL | Original filename as provided during upload |

**Example row:**
```
image_id: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
mime_type: "image/jpeg"
file_size: 2048576
original_file_name: "vacation_photo.jpg"
```

### tags

Stores image tags in a many-to-many relationship with images.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `image_id` | TEXT | PRIMARY KEY (composite), FOREIGN KEY | Reference to `images(image_id)` |
| `tag` | TEXT | PRIMARY KEY (composite) | Tag label assigned to the image |

**Constraints:**
- **Primary Key**: Composite key on (`image_id`, `tag`) ensures each image-tag combination is unique
- **Foreign Key**: `image_id` references `images(image_id)` with `ON DELETE CASCADE` (deleting an image removes all its tags)

**Example rows:**
```
image_id: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0" | tag: "vacation"
image_id: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0" | tag: "beach"
```

## Indexes

| Name | Table | Column(s) | Purpose |
|------|-------|-----------|---------|
| `idx_tags_tag` | tags | tag | Speed up queries filtering by tag name |
| `idx_tags_image_id` | tags | image_id | Speed up queries fetching tags for an image |

## Relationships

```
images (1) ──── (many) tags
```

- One image can have multiple tags
- Deleting an image automatically deletes all associated tags (ON DELETE CASCADE)
- Adding a tag requires an existing image (foreign key constraint enforced)

## Notes

- **Image Deduplication**: The `image_id` is the SHA1 hash of the file content, so identical files uploaded multiple times will reference the same image record
- **Case Sensitivity**: Tags are case-sensitive (e.g., `"Vacation"` and `"vacation"` are different tags)
