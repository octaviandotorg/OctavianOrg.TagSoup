import json
import hashlib
from pathlib import Path
import shutil

from fastapi.testclient import TestClient
import pytest

from main import app
from services.image_service import UPLOAD_DIR
from db import init_db


@pytest.fixture(autouse=True)
def cleanup_uploads():
    """Clean up uploads directory and initialize database before and after each test"""
    from db import DB_PATH

    # Delete old database to start fresh
    if DB_PATH.exists():
        DB_PATH.unlink()

    # Initialize database
    init_db()

    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    yield

    # Cleanup after test
    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestUploadImage:
    """Tests for the uploadImage endpoint"""

    def test_upload_valid_jpeg(self, client, valid_test_image):
        """Test successful upload of a valid JPEG image"""
        response = client.post(
            "/api/image/uploadImage",
            files={"file": ("test.jpg", valid_test_image, "image/jpeg")}
        )

        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["mime_type"] == "image/jpeg"
        assert data["original_filename"] == "test.jpg"
        assert data["file_size"] > 0

        # Verify Location header
        assert "Location" in response.headers
        assert data["id"] in response.headers["Location"]

        # Verify file was saved
        saved_file = UPLOAD_DIR / data["id"]
        assert saved_file.exists()
        assert saved_file.is_file()

    def test_upload_valid_png(self, client, valid_test_png):
        """Test successful upload of a valid PNG image"""
        response = client.post(
            "/api/image/uploadImage",
            files={"file": ("test.png", valid_test_png, "image/png")}
        )

        assert response.status_code == 201

        data = response.json()
        assert data["mime_type"] == "image/png"
        assert data["original_filename"] == "test.png"

        # Verify file was saved
        saved_file = UPLOAD_DIR / data["id"]
        assert saved_file.exists()

    def test_upload_invalid_mime_type(self, client):
        """Test upload rejection with invalid MIME type"""
        response = client.post(
            "/api/image/uploadImage",
            files={"file": ("test.txt", b"This is not an image", "text/plain")}
        )

        assert response.status_code == 400

        data = response.json()
        assert "not allowed" in data["detail"].lower()

    def test_upload_oversized_file(self, client, oversized_test_image):
        """Test upload rejection when file exceeds 50 MB limit"""
        response = client.post(
            "/api/image/uploadImage",
            files={"file": ("large.jpg", oversized_test_image, "image/jpeg")}
        )

        assert response.status_code == 413

        data = response.json()
        assert "exceeds" in data["detail"].lower()
        assert "50" in data["detail"]

    def test_upload_generates_sha1_id(self, client, valid_test_image):
        """Test that upload generates correct SHA1 hash as ID"""
        # Calculate expected SHA1
        file_content = valid_test_image.read()
        expected_sha1 = hashlib.sha1(file_content).hexdigest()

        # Upload
        valid_test_image.seek(0)
        response = client.post(
            "/api/image/uploadImage",
            files={"file": ("test.jpg", valid_test_image, "image/jpeg")}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == expected_sha1

        # Verify file is saved with SHA1 name
        saved_file = UPLOAD_DIR / expected_sha1
        assert saved_file.exists()

    def test_upload_response_json_structure(self, client, valid_test_image):
        """Test that response contains all required ImageInfo fields"""
        response = client.post(
            "/api/image/uploadImage",
            files={"file": ("test.jpg", valid_test_image, "image/jpeg")}
        )

        assert response.status_code == 201

        data = response.json()
        required_fields = {"id", "mime_type", "file_size", "original_filename"}
        assert required_fields.issubset(data.keys())

        # Verify field types
        assert isinstance(data["id"], str)
        assert isinstance(data["mime_type"], str)
        assert isinstance(data["file_size"], int)
        assert isinstance(data["original_filename"], str)

    def test_upload_duplicate_file_same_id(self, client, valid_test_image):
        """Test that uploading the same file twice generates the same ID"""
        # First upload
        valid_test_image.seek(0)
        response1 = client.post(
            "/api/image/uploadImage",
            files={"file": ("test.jpg", valid_test_image, "image/jpeg")}
        )
        id1 = response1.json()["id"]

        # Second upload of same file
        valid_test_image.seek(0)
        response2 = client.post(
            "/api/image/uploadImage",
            files={"file": ("test.jpg", valid_test_image, "image/jpeg")}
        )
        id2 = response2.json()["id"]

        assert id1 == id2
