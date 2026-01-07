import json
import pytest
from pathlib import Path
from io import BytesIO
from fastapi.testclient import TestClient

from main import app
from db import init_db

DB_PATH = Path(__file__).parent.parent / "images.db"
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
THUMBNAIL_DIR = Path(__file__).parent.parent / "thumbnails"


@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test."""
    # Clean up old database
    if DB_PATH.exists():
        DB_PATH.unlink()

    # Initialize fresh database
    init_db()

    # Clean up upload/thumbnail directories
    if UPLOAD_DIR.exists():
        for file in UPLOAD_DIR.glob("*"):
            if file.is_file():
                file.unlink()
    else:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    if THUMBNAIL_DIR.exists():
        for file in THUMBNAIL_DIR.glob("*"):
            if file.is_file():
                file.unlink()
    else:
        THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

    yield

    # Cleanup after test
    if DB_PATH.exists():
        DB_PATH.unlink()


class TestPagination:
    """Test pagination functionality for getImagesInfo endpoint."""

    def test_get_images_info_requires_tag_parameter(self):
        """Test that tag parameter is required."""
        client = TestClient(app)
        response = client.get("/api/image/getImagesInfo")
        assert response.status_code == 422  # Unprocessable Entity

    def test_get_images_info_empty_results(self):
        """Test pagination with no images."""
        client = TestClient(app)
        response = client.get("/api/image/getImagesInfo?tag=untagged")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["next_cursor"] is None
        assert data["page_size"] == 20
        assert data["has_more"] is False

    def test_get_images_info_single_page(self):
        """Test pagination with results that fit in single page."""
        client = TestClient(app)

        # Upload 5 images
        for i in range(5):
            image_data = b"fake image data " + str(i).encode()
            files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}
            response = client.post("/api/image/uploadImage", files=files)
            assert response.status_code == 201

        # Get all untagged images (default page_size=20)
        response = client.get("/api/image/getImagesInfo?tag=untagged")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["next_cursor"] is None
        assert data["page_size"] == 20
        assert data["has_more"] is False

    def test_get_images_info_multiple_pages(self):
        """Test cursor-based pagination across multiple pages."""
        client = TestClient(app)

        # Upload 25 images
        image_ids = []
        for i in range(25):
            image_data = b"fake image data " + str(i).encode()
            files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}
            response = client.post("/api/image/uploadImage", files=files)
            assert response.status_code == 201
            image_ids.append(response.json()["id"])

        # Get first page (page_size=10)
        response = client.get("/api/image/getImagesInfo?tag=untagged&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page_size"] == 10
        assert data["has_more"] is True
        assert data["next_cursor"] is not None
        first_page_ids = [item["id"] for item in data["items"]]
        first_cursor = data["next_cursor"]

        # Get second page
        response = client.get(f"/api/image/getImagesInfo?tag=untagged&page_size=10&cursor={first_cursor}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page_size"] == 10
        assert data["has_more"] is True
        second_page_ids = [item["id"] for item in data["items"]]
        second_cursor = data["next_cursor"]

        # Get third page
        response = client.get(f"/api/image/getImagesInfo?tag=untagged&page_size=10&cursor={second_cursor}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page_size"] == 10
        assert data["has_more"] is False
        assert data["next_cursor"] is None
        third_page_ids = [item["id"] for item in data["items"]]

        # Verify no duplicates across pages
        all_page_ids = first_page_ids + second_page_ids + third_page_ids
        assert len(all_page_ids) == len(set(all_page_ids))
        assert len(all_page_ids) == 25

    def test_get_images_info_page_size_validation(self):
        """Test page_size validation."""
        client = TestClient(app)

        # Test page_size < 1
        response = client.get("/api/image/getImagesInfo?tag=untagged&page_size=0")
        assert response.status_code == 422

        # Test page_size > 100
        response = client.get("/api/image/getImagesInfo?tag=untagged&page_size=101")
        assert response.status_code == 422

    def test_get_images_info_default_page_size(self):
        """Test default page_size is 20."""
        client = TestClient(app)

        # Upload 5 images
        for i in range(5):
            image_data = b"fake image data " + str(i).encode()
            files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}
            response = client.post("/api/image/uploadImage", files=files)
            assert response.status_code == 201

        response = client.get("/api/image/getImagesInfo?tag=untagged")
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 20

    def test_get_images_info_exact_page_size_results(self):
        """Test when results exactly match page_size."""
        client = TestClient(app)

        # Upload exactly 10 images
        for i in range(10):
            image_data = b"fake image data " + str(i).encode()
            files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}
            response = client.post("/api/image/uploadImage", files=files)
            assert response.status_code == 201

        response = client.get("/api/image/getImagesInfo?tag=untagged&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["has_more"] is False
        assert data["next_cursor"] is None

    def test_get_images_info_tag_filtering(self):
        """Test that only images with specified tag are returned."""
        client = TestClient(app)

        # Upload one image
        image_data = b"fake image data"
        files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}
        response = client.post("/api/image/uploadImage", files=files)
        assert response.status_code == 201

        # Get with 'untagged' tag - should find 1
        response = client.get("/api/image/getImagesInfo?tag=untagged")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["tags"] == ["untagged"]

        # Get with different tag - should find 0
        response = client.get("/api/image/getImagesInfo?tag=vacation")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["has_more"] is False

    def test_get_images_info_response_structure(self):
        """Test response structure and field types."""
        client = TestClient(app)

        # Upload one image
        image_data = b"fake image data"
        files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}
        response = client.post("/api/image/uploadImage", files=files)
        assert response.status_code == 201

        response = client.get("/api/image/getImagesInfo?tag=untagged")
        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "items" in data
        assert "next_cursor" in data
        assert "page_size" in data
        assert "has_more" in data

        # Check types
        assert isinstance(data["items"], list)
        assert isinstance(data["next_cursor"], type(None))
        assert isinstance(data["page_size"], int)
        assert isinstance(data["has_more"], bool)

        # Check item structure
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert "id" in item
        assert "mime_type" in item
        assert "file_size" in item
        assert "original_filename" in item
        assert "tags" in item
        assert isinstance(item["tags"], list)

    def test_get_images_info_custom_page_size(self):
        """Test pagination with custom page sizes."""
        client = TestClient(app)

        # Upload 15 images
        for i in range(15):
            image_data = b"fake image data " + str(i).encode()
            files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}
            response = client.post("/api/image/uploadImage", files=files)
            assert response.status_code == 201

        # Test with page_size=5
        response = client.get("/api/image/getImagesInfo?tag=untagged&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page_size"] == 5
        assert data["has_more"] is True

        # Test with page_size=100 (max)
        response = client.get("/api/image/getImagesInfo?tag=untagged&page_size=100")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 15
        assert data["page_size"] == 100
        assert data["has_more"] is False
