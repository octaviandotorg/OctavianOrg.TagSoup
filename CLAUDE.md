# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TagSoup is a web application for managing image files, performing face detection and recognition, and tagging images. The UI consists of a large main window for displaying image thumbnails, an input box for searching for image tags and updating the display to show thumbnails of images matching the selected tags. Facial detection and recognition features will be added later. To the right of the thumbnail display area is a vertical list of all defined image tags - clicking on one of these tags will add the tag to the search box and the display will be updated to reflect images that match all of the selected tags.

## Development Commands


## Architecture

The UI frontend is constructed using the Svelte framework. The REST API backend uses python and the FastAPI framework.

## API Versioning

All REST APIs support versioning via a "X-API-Version" header, using a semantic versioning.

## Image API

The image API supports the following operations:

* /api/image/uploadImage
* /api/image/getImage
* /api/image/getImageInfo
* /api/image/getImageThumbnail

## Testing

How to Run Tests:
cd backend
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
pytest tests/test_image_upload.py -v

  1. Start the frontend: npm run dev (from frontend/ directory)
  2. Start the backend: python backend/main.py
  3. Navigate to http://localhost:5173
  4. Select an image file and click Upload
  5. View the confirmation modal with the JSON response
