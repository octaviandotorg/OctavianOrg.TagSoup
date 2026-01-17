// API service for TagSoup backend

async function getImagesInfo(pageSize = 20, cursor = null, tags = []) {
  const params = new URLSearchParams();
  if (pageSize) params.append('page_size', pageSize);
  if (cursor) params.append('cursor', cursor);

  // Add multiple tag parameters
  if (tags && tags.length > 0) {
    tags.forEach(tag => params.append('tag', tag));
  }

  const response = await fetch(`/api/image/getImagesInfo?${params}`, {
    method: 'GET',
    headers: {
      'X-API-Version': '1.0.0',
    },
  });

  const result = await response.json();

  if (!result.success) {
    throw new Error(`${result.error_type}: ${result.message}`);
  }

  return result.data;
}

async function getImage(imageId) {
  const response = await fetch(`/api/image/getImage/${encodeURIComponent(imageId)}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch image ${imageId}`);
  }

  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

async function getImageThumbnail(imageId) {
  const response = await fetch(`/api/image/getImageThumbnail/${encodeURIComponent(imageId)}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch thumbnail for image ${imageId}`);
  }

  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

async function uploadImage(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/image/uploadImage', {
    method: 'POST',
    body: formData,
  });

  const result = await response.json();

  if (!result.success) {
    throw new Error(`${result.error_type}: ${result.message}`);
  }

  return result.data;
}

async function addImageTag(imageId, tag) {
  const response = await fetch(`/api/image/${encodeURIComponent(imageId)}/addImageTag/${encodeURIComponent(tag)}`, {
    method: 'POST'
  });

  const result = await response.json();

  if (!result.success) {
    throw new Error(`${result.error_type}: ${result.message}`);
  }
}

async function deleteImageTag(imageId, tag) {
  const response = await fetch(`/api/image/${encodeURIComponent(imageId)}/deleteImageTag/${encodeURIComponent(tag)}`, {
    method: 'POST'
  });

  const result = await response.json();

  if (!result.success) {
    throw new Error(`${result.error_type}: ${result.message}`);
  }
}

async function getImageTags() {
  const response = await fetch(`/api/image/getImageTags`, {
    method: 'GET'
  });

  const result = await response.json();

  if (!result.success) {
    throw new Error(`${result.error_type}: ${result.message}`);
  }

  return result.data;
}

export { addImageTag, deleteImageTag, getImagesInfo, getImage, getImageTags, getImageThumbnail, uploadImage };
