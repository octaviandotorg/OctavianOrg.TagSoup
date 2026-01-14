# TagSoup

A web application for managing, tagging, and searching through your image collection. TagSoup provides an intuitive interface for organizing images with flexible tagging, fast searching, and upcoming facial recognition capabilities.

## Features

- **Image Upload** - Upload images with automatic deduplication via SHA1 hashing
- **Tag Management** - Add, remove, and manage tags on images
- **Tag Filtering** - Filter images by one or more tags (AND logic)
- **Tag Autocomplete** - Smart suggestions as you type using suffix tree search
- **Image Browsing** - Responsive thumbnail grid with pagination
- **Full Image View** - Click thumbnails to view full-size images with tag management
- **RESTful API** - Fully versioned REST API for programmatic access

## Coming Soon

- Facial detection and recognition
- Advanced search capabilities
- Batch tagging operations

## Tech Stack

### Frontend
- **Svelte 4** - Lightweight, reactive UI framework
- **Vite** - Fast development server and build tool
- **JavaScript** - Tag suggestion engine with suffix tree implementation

### Backend
- **Python 3** - Core language
- **FastAPI** - Modern, fast web framework with async support
- **SQLite** - Lightweight database for metadata
- **Pillow** - Image processing (thumbnails, format detection)
- **Uvicorn** - ASGI server

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/TagSoup.git
   cd TagSoup
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv

   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. **Start the backend** (from `backend/` directory)
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`

2. **Start the frontend** (from `frontend/` directory)
   ```bash
   npm run dev
   ```
   The UI will be available at `http://localhost:5173`

3. **Open your browser**
   Navigate to `http://localhost:5173`

## Project Structure

```
TagSoup/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── db.py                      # Database initialization and connection
│   ├── requirements.txt           # Python dependencies
│   ├── models/                    # Pydantic models for API responses
│   │   ├── image_info.py
│   │   └── paginated_images_response.py
│   ├── routers/                   # API route handlers
│   │   └── images.py
│   ├── services/                  # Business logic layer
│   │   └── image_service.py
│   ├── repositories/              # Data access layer
│   │   └── image_repository.py
│   └── tests/                     # Test suite
│       ├── test_image_upload.py
│       └── test_pagination.py
│
├── frontend/
│   ├── src/
│   │   ├── App.svelte             # Main application component
│   │   ├── api.js                 # API client
│   │   ├── suffix-tree.js         # Tag suggestion engine
│   │   ├── main.js                # Application entry point
│   │   ├── ThumbnailGrid.svelte   # Image grid component
│   │   ├── FullImageDisplay.svelte # Full image view component
│   │   ├── PaginationControls.svelte
│   │   └── Modal.svelte           # Reusable modal component
│   ├── package.json
│   ├── vite.config.js
│   └── svelte.config.js
│
├── DATABASE_SCHEMA.md             # Database documentation
└── README.md                      # This file
```

## API Documentation

### Base URL
```
http://localhost:8000/api/image
```

### Endpoints

#### Upload Image
```
POST /uploadImage
Content-Type: multipart/form-data

Request:
- file: Image file to upload

Response: 201 Created
{
  "id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
  "mime_type": "image/jpeg",
  "file_size": 2048576,
  "original_filename": "vacation_photo.jpg",
  "tags": []
}
```

#### Get Images Info
```
GET /getImagesInfo?page_size=20&tag=vacation&tag=beach&cursor=<cursor>

Query Parameters:
- page_size: Number of items per page (1-100, default: 20)
- tag: Filter by tag (can be specified multiple times)
- cursor: Pagination cursor from previous response

Response: 200 OK
{
  "items": [
    {
      "id": "...",
      "mime_type": "image/jpeg",
      "file_size": 2048576,
      "original_filename": "photo.jpg",
      "tags": ["vacation", "beach"]
    }
  ],
  "next_cursor": "...",
  "has_more": true,
  "total_count": 150
}
```

#### Get Image
```
GET /getImage/{image_id}

Response: 200 OK
- Returns the full image file with appropriate Content-Type header
```

#### Get Image Thumbnail
```
GET /getImageThumbnail/{image_id}

Response: 200 OK
- Returns a WebP thumbnail of the image
```

#### Get Image Info
```
GET /getImageInfo/{image_id}

Response: 200 OK
{
  "id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
  "mime_type": "image/jpeg",
  "file_size": 2048576,
  "original_filename": "photo.jpg",
  "tags": ["vacation", "beach"]
}
```

#### Add Image Tag
```
POST /{image_id}/addImageTag/{tag}

Response: 200 OK
```

#### Delete Image Tag
```
POST /{image_id}/deleteImageTag/{tag}

Response: 200 OK
```

#### Get All Tags
```
GET /getImageTags

Response: 200 OK
["vacation", "beach", "family", ...]
```

#### Health Check
```
GET /health

Response: 200 OK
{"status": "ok"}
```

## Database Schema

The application uses SQLite with the following tables:

### images
Stores core image metadata, identified by SHA1 hash for deduplication.

| Column | Type | Description |
|--------|------|-------------|
| `image_id` | TEXT PRIMARY KEY | SHA1 hash of the image file |
| `mime_type` | TEXT NOT NULL | MIME type (e.g., `image/jpeg`) |
| `file_size` | INTEGER NOT NULL | File size in bytes |
| `original_file_name` | TEXT NOT NULL | Original filename provided during upload |

### tags
Stores the many-to-many relationship between images and tags.

| Column | Type | Description |
|--------|------|-------------|
| `image_id` | TEXT PRIMARY KEY (composite) | Reference to `images(image_id)` |
| `tag` | TEXT PRIMARY KEY (composite) | Tag label assigned to the image |

For more details, see [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md)

## Running Tests

```bash
cd backend

# Activate virtual environment
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_image_upload.py -v
```

## Development

### Building the Frontend
```bash
cd frontend
npm run build
```
Output is generated in `frontend/dist/`

### Code Style
- **Backend**: Python with FastAPI conventions
- **Frontend**: Svelte with scoped styling

## API Versioning

All REST API endpoints support versioning via the `X-API-Version` header using semantic versioning:

```bash
curl -H "X-API-Version: 0.1.0" http://localhost:8000/api/image/getImagesInfo
```

## File Organization

- **Images**: Stored in `backend/uploads/` directory
- **Thumbnails**: Generated and cached in `backend/thumbnails/` directory
- **Database**: SQLite database file in `backend/` directory

## Key Design Decisions

1. **Image Deduplication**: Images are identified by SHA1 hash of file content, preventing duplicate uploads
2. **Cursor-Based Pagination**: More efficient than offset-based pagination for large datasets
3. **Tag Suffix Tree**: Provides fast, efficient tag suggestion with O(log n) lookup performance
4. **Thumbnail Caching**: WebP thumbnails are generated once and cached for performance
5. **RESTful Architecture**: Standard HTTP methods and status codes for predictable client interaction

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License

## Support

For issues, questions, or suggestions, please open an issue on [GitHub](https://github.com/yourusername/TagSoup/issues).

---

Built with ❤️ using Python, FastAPI, and Svelte
