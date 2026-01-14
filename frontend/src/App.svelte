<script>
  import Modal from './Modal.svelte';
  import ThumbnailGrid from './ThumbnailGrid.svelte';
  import FullImageDisplay from './FullImageDisplay.svelte';
  import { onMount } from 'svelte';
  import { getImagesInfo, getImage, getImageThumbnail, uploadImage, addImageTag, deleteImageTag, getImageTags } from './api.js';
  import { SuffixTree } from './suffix-tree.js';

  let pages = [];
  let currentPage = 1;
  let selectedFile = null;
  let isUploading = false;
  let isLoadingImages = false;
  let showModal = false;
  let showUploadModal = false;
  let modalData = null;
  let modalType = 'success';
  let modalTitle = '';
  let fileInput;
  let selectedTags = [];
  let tagInput = '';
  let selectedImageForDisplay = null;
  let fullImageUrl = null;
  let isLoadingFullImage = false;
  let showTagModal = false;
  let tagInputValue = '';
  let isAddingTag = false;
  let allTags = [];
  let tagTree = null;
  let tagSuggestions = [];
  let showTagSuggestions = false;
  let selectedSuggestionIndex = -1;
  let modalTagSuggestions = [];
  let showModalTagSuggestions = false;
  let selectedModalSuggestionIndex = -1;

  $: images = pages[currentPage - 1]?.images || [];
  $: totalPages = pages.length;

  onMount(async () => {
    // Load images and tags concurrently
    await Promise.all([loadImages(), loadTags()]);
  });

  async function loadTags() {
    try {
      const tags = await getImageTags();
      allTags = tags;

      // Build suffix tree for tag suggestions
      tagTree = new SuffixTree();
      for (const tag of tags) {
        tagTree.addString(tag.toLowerCase(), tag);
      }
    } catch (error) {
      console.error('Failed to load tags:', error);
    }
  }

  async function loadPage(cursor = null, tags = []) {
    try {
      const data = await getImagesInfo(20, cursor, tags);
      const imageInfoList = data.items || [];

      // Fetch thumbnails in parallel
      const imagePromises = imageInfoList.map(async (info) => {
        try {
          const thumbnailUrl = await getImageThumbnail(info.id);
          return {
            ...info,
            thumbnailUrl,
          };
        } catch (error) {
          console.error(`Failed to load thumbnail for ${info.id}:`, error);
          return {
            ...info,
            thumbnailUrl: null,
          };
        }
      });

      const imagesWithThumbnails = await Promise.all(imagePromises);

      return {
        images: imagesWithThumbnails,
        nextCursor: data.next_cursor,
        hasMore: data.has_more,
      };
    } catch (error) {
      console.error('Failed to load page:', error);
      modalType = 'error';
      modalTitle = 'Failed to Load Images';
      modalData = { detail: error.message };
      showModal = true;
      return null;
    }
  }

  async function loadImages(tags = []) {
    isLoadingImages = true;
    pages = [];
    currentPage = 1;

    try {
      const pageData = await loadPage(null, tags);
      if (pageData) {
        pages = [pageData];
        // Load next page if available
        if (pageData.hasMore) {
          loadNextPage(pageData.nextCursor, tags);
        }
      }
    } finally {
      isLoadingImages = false;
    }
  }

  async function loadNextPage(cursor, tags = []) {
    try {
      const pageData = await loadPage(cursor, tags);
      if (pageData) {
        pages = [...pages, pageData];
        // Keep loading more pages up to a reasonable limit
        if (pageData.hasMore && pages.length < 10) {
          loadNextPage(pageData.nextCursor, tags);
        }
      }
    } catch (error) {
      console.error('Failed to load next page:', error);
    }
  }

  function handlePageChange(pageNum) {
    currentPage = pageNum;
  }

  function handleFileSelect(event) {
    selectedFile = event.target.files[0] || null;
    if (selectedFile) {
      handleUpload();
    }
  }

  async function handleUpload() {
    if (!selectedFile) return;

    isUploading = true;
    try {
      const data = await uploadImage(selectedFile);
      modalType = 'success';
      modalTitle = 'Upload Successful';
      modalData = data;
      showUploadModal = true;

      // Reload images after successful upload
      await loadImages();
    } catch (error) {
      modalType = 'error';
      modalTitle = 'Upload Failed';
      modalData = { detail: error.message };
      showUploadModal = true;
    } finally {
      isUploading = false;
    }
  }

  function closeModal() {
    showUploadModal = false;
    showModal = false;
    if (modalType === 'success') {
      selectedFile = null;
      fileInput.value = '';
    }
  }

  function addTag() {
    const trimmed = tagInput.trim();
    if (trimmed && !selectedTags.includes(trimmed)) {
      selectedTags = [...selectedTags, trimmed];
      tagInput = '';
      showTagSuggestions = false;
      selectedSuggestionIndex = -1;
      loadImages(selectedTags);
    }
  }

  function removeTag(tag) {
    selectedTags = selectedTags.filter(t => t !== tag);
    loadImages(selectedTags);
  }

  function searchTagSuggestions(input) {
    if (!input || input.length === 0 || !tagTree) {
      tagSuggestions = [];
      showTagSuggestions = false;
      selectedSuggestionIndex = -1;
      return;
    }

    const results = tagTree.search(input.toLowerCase(), { limit: 10 });

    // Extract unique tag names from results and filter out already selected tags
    const uniqueTags = new Set();
    for (const result of results.matches) {
      if (!selectedTags.includes(result.stringId)) {
        uniqueTags.add(result.stringId);
      }
    }

    tagSuggestions = Array.from(uniqueTags);
    showTagSuggestions = tagSuggestions.length > 0;
    selectedSuggestionIndex = -1; // Reset selection when suggestions change
  }

  function handleTagInputKeydown(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      if (showTagSuggestions && selectedSuggestionIndex >= 0) {
        // Select the highlighted suggestion
        selectSuggestedTag(tagSuggestions[selectedSuggestionIndex]);
      } else {
        // Add the typed tag
        addTag();
      }
    } else if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (showTagSuggestions && tagSuggestions.length > 0) {
        selectedSuggestionIndex = Math.min(
          selectedSuggestionIndex + 1,
          tagSuggestions.length - 1
        );
      }
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      if (showTagSuggestions && selectedSuggestionIndex > 0) {
        selectedSuggestionIndex--;
      }
    }
  }

  function selectSuggestedTag(tag) {
    tagInput = tag;
    showTagSuggestions = false;
    addTag();
  }

  function searchModalTagSuggestions(input) {
    if (!input || input.length === 0 || !tagTree) {
      modalTagSuggestions = [];
      showModalTagSuggestions = false;
      selectedModalSuggestionIndex = -1;
      return;
    }

    const results = tagTree.search(input.toLowerCase(), { limit: 10 });

    // Extract unique tag names from results
    const uniqueTags = new Set();
    for (const result of results.matches) {
      uniqueTags.add(result.stringId);
    }

    modalTagSuggestions = Array.from(uniqueTags);
    showModalTagSuggestions = modalTagSuggestions.length > 0;
    selectedModalSuggestionIndex = -1; // Reset selection when suggestions change
  }

  function selectModalSuggestedTag(tag) {
    tagInputValue = tag;
    showModalTagSuggestions = false;
    selectedModalSuggestionIndex = -1;
  }

  function handleModalTagInputKeydown(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      if (showModalTagSuggestions && selectedModalSuggestionIndex >= 0) {
        // Select the highlighted suggestion
        selectModalSuggestedTag(modalTagSuggestions[selectedModalSuggestionIndex]);
      } else {
        // Submit the tag
        submitTag();
      }
    } else if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (showModalTagSuggestions && modalTagSuggestions.length > 0) {
        selectedModalSuggestionIndex = Math.min(
          selectedModalSuggestionIndex + 1,
          modalTagSuggestions.length - 1
        );
      }
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      if (showModalTagSuggestions && selectedModalSuggestionIndex > 0) {
        selectedModalSuggestionIndex--;
      }
    }
  }

  async function handleSelectImage(event) {
    const image = event.detail;
    selectedImageForDisplay = image;
    isLoadingFullImage = true;

    try {
      fullImageUrl = await getImage(image.id);
    } catch (error) {
      console.error('Failed to load full image:', error);
      modalType = 'error';
      modalTitle = 'Failed to Load Image';
      modalData = { detail: error.message };
      showModal = true;
      selectedImageForDisplay = null;
    } finally {
      isLoadingFullImage = false;
    }
  }

  function handleCloseFullImage() {
    selectedImageForDisplay = null;
    fullImageUrl = null;
  }

  function handleAddTag() {
    showTagModal = true;
    tagInputValue = '';
  }

  async function handleDeleteTag(tag) {
    try {
      await deleteImageTag(selectedImageForDisplay.id, tag);

      // Update the image info by removing the tag
      selectedImageForDisplay.tags = selectedImageForDisplay.tags.filter(t => t !== tag);
    } catch (error) {
      modalType = 'error';
      modalTitle = 'Failed to Remove Tag';
      modalData = { detail: error.message };
      showModal = true;
    }
  }

  function closeTagModal() {
    showTagModal = false;
    tagInputValue = '';
    modalTagSuggestions = [];
    showModalTagSuggestions = false;
    selectedModalSuggestionIndex = -1;
  }

  async function submitTag() {
    const tag = tagInputValue.trim();
    if (!tag) return;

    isAddingTag = true;
    try {
      await addImageTag(selectedImageForDisplay.id, tag);

      // Update the image info with the new tag
      if (!selectedImageForDisplay.tags.includes(tag)) {
        selectedImageForDisplay.tags = [...selectedImageForDisplay.tags, tag];
      }

      // Update tags list and suffix tree if this is a new tag
      if (!allTags.includes(tag)) {
        allTags = [...allTags, tag];
        if (tagTree) {
          tagTree.addString(tag.toLowerCase(), tag);
        }
      }

      closeTagModal();
    } catch (error) {
      modalType = 'error';
      modalTitle = 'Failed to Add Tag';
      modalData = { detail: error.message };
      showModal = true;
    } finally {
      isAddingTag = false;
    }
  }

  function handleTagModalKeydown(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      submitTag();
    }
  }
</script>

<div class="container">
  <header class="app-header">
    <div class="header-content">
      <div class="header-title">
        <h1>TagSoup</h1>
        <p>Image management and tagging</p>
      </div>
    </div>
    <div class="upload-button-container">
      <input
        type="file"
        accept="image/*"
        on:change={handleFileSelect}
        bind:this={fileInput}
        id="file-input"
        style="display: none;"
      />
      <button
        on:click={() => fileInput.click()}
        class="upload-btn-fixed"
        title="Upload a new image"
      >
        + Upload
      </button>
    </div>
  </header>

  <main class="main-content">
    <div class="tag-section">
      <div class="tag-input-wrapper">
        <div class="tag-input-container">
          <input
            type="text"
            placeholder="Add tags to filter images..."
            bind:value={tagInput}
            on:keydown={handleTagInputKeydown}
            on:input={(e) => searchTagSuggestions(e.target.value)}
            class="tag-input"
          />
          <button on:click={addTag} class="add-tag-btn">Add</button>
        </div>
        {#if showTagSuggestions && tagSuggestions.length > 0}
          <div class="tag-suggestions">
            {#each tagSuggestions as suggestion, index (suggestion)}
              <button
                class="tag-suggestion-item"
                class:selected={index === selectedSuggestionIndex}
                on:click={() => selectSuggestedTag(suggestion)}
                type="button"
              >
                {suggestion}
              </button>
            {/each}
          </div>
        {/if}
      </div>
      {#if selectedTags.length > 0}
        <div class="tags-display">
          {#each selectedTags as tag (tag)}
            <div class="tag-chip">
              {tag}
              <button
                class="remove-tag-btn"
                on:click={() => removeTag(tag)}
                aria-label="Remove tag"
              >
                ×
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <ThumbnailGrid
      {images}
      {currentPage}
      {totalPages}
      isLoading={isLoadingImages}
      on:selectImage={handleSelectImage}
      on:pageChange={(e) => handlePageChange(e.detail)}
    />
  </main>
</div>

{#if selectedImageForDisplay && fullImageUrl}
  <FullImageDisplay
    imageUrl={fullImageUrl}
    imageInfo={selectedImageForDisplay}
    onClose={handleCloseFullImage}
    onAddTag={handleAddTag}
    onDeleteTag={handleDeleteTag}
  />
{/if}

{#if showTagModal}
  <div class="tag-modal-overlay" on:click={closeTagModal}>
    <div class="tag-modal-content" on:click|stopPropagation>
      <h2>Add Tag to Image</h2>
      <p>Enter a tag name for this image:</p>
      <div class="tag-modal-input-wrapper">
        <input
          type="text"
          placeholder="e.g., vacation, family, favorite..."
          bind:value={tagInputValue}
          on:keydown={handleModalTagInputKeydown}
          on:input={(e) => searchModalTagSuggestions(e.target.value)}
          autoFocus
          disabled={isAddingTag}
          class="tag-modal-input"
        />
        {#if showModalTagSuggestions && modalTagSuggestions.length > 0}
          <div class="tag-modal-suggestions">
            {#each modalTagSuggestions as suggestion, index (suggestion)}
              <button
                class="tag-modal-suggestion-item"
                class:selected={index === selectedModalSuggestionIndex}
                on:click={() => selectModalSuggestedTag(suggestion)}
                type="button"
                disabled={isAddingTag}
              >
                {suggestion}
              </button>
            {/each}
          </div>
        {/if}
      </div>
      <div class="tag-modal-buttons">
        <button
          on:click={closeTagModal}
          disabled={isAddingTag}
          class="tag-modal-cancel-btn"
        >
          Cancel
        </button>
        <button
          on:click={submitTag}
          disabled={isAddingTag || !tagInputValue.trim()}
          class="tag-modal-submit-btn"
        >
          {isAddingTag ? 'Adding...' : 'Add Tag'}
        </button>
      </div>
    </div>
  </div>
{/if}

<Modal
  isOpen={showUploadModal || showModal}
  title={modalTitle}
  type={modalType}
  on:close={closeModal}
>
  <pre>{JSON.stringify(modalData, null, 2)}</pre>
</Modal>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
  }

  .container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  .app-header {
    background-color: white;
    border-bottom: 1px solid #ddd;
    padding: 16px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }

  .header-content {
    flex: 1;
  }

  .header-title h1 {
    margin: 0;
    font-size: 28px;
    color: #333;
    font-weight: 600;
  }

  .header-title p {
    margin: 4px 0 0 0;
    font-size: 13px;
    color: #999;
  }

  .upload-button-container {
    display: flex;
    gap: 8px;
  }

  .upload-btn-fixed {
    background-color: #4caf50;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background-color 0.2s;
    white-space: nowrap;
  }

  .upload-btn-fixed:hover {
    background-color: #45a049;
  }

  .upload-btn-fixed:focus {
    outline: 2px solid #2e7d32;
    outline-offset: 2px;
  }

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding: 20px;
  }

  .tag-section {
    margin-bottom: 20px;
    background-color: white;
    padding: 16px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .tag-input-wrapper {
    display: flex;
    flex-direction: column;
    gap: 0;
    margin-bottom: 12px;
    position: relative;
  }

  .tag-input-container {
    display: flex;
    gap: 8px;
  }

  .tag-input {
    flex: 1;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    font-family: Arial, sans-serif;
  }

  .tag-input:focus {
    outline: none;
    border-color: #4caf50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
  }

  .add-tag-btn {
    padding: 10px 16px;
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background-color 0.2s;
  }

  .add-tag-btn:hover {
    background-color: #45a049;
  }

  .tag-suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: white;
    border: 1px solid #ddd;
    border-top: none;
    border-radius: 0 0 4px 4px;
    max-height: 200px;
    overflow-y: auto;
    z-index: 10;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .tag-suggestion-item {
    width: 100%;
    text-align: left;
    padding: 10px 12px;
    border: none;
    background-color: white;
    cursor: pointer;
    font-size: 14px;
    font-family: Arial, sans-serif;
    color: #333;
    transition: background-color 0.15s;
  }

  .tag-suggestion-item:hover {
    background-color: #f5f5f5;
  }

  .tag-suggestion-item.selected {
    background-color: #e3f2fd;
    color: #1976d2;
    font-weight: 500;
  }

  .tag-suggestion-item.selected:hover {
    background-color: #bbdefb;
  }

  .tag-suggestion-item:active {
    background-color: #e8e8e8;
  }

  .tags-display {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .tag-chip {
    background-color: #e8f5e9;
    border: 1px solid #4caf50;
    color: #2e7d32;
    padding: 6px 12px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }

  .remove-tag-btn {
    background: none;
    border: none;
    color: #2e7d32;
    font-size: 18px;
    cursor: pointer;
    padding: 0;
    display: flex;
    align-items: center;
    line-height: 1;
  }

  .remove-tag-btn:hover {
    color: #1b5e20;
  }

  .tag-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1001;
  }

  .tag-modal-content {
    background-color: white;
    border-radius: 8px;
    padding: 28px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    max-width: 400px;
    width: 90%;
    animation: slideUp 0.2s ease-out;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .tag-modal-content h2 {
    margin: 0 0 8px 0;
    font-size: 18px;
    color: #333;
    font-weight: 600;
  }

  .tag-modal-content p {
    margin: 0 0 16px 0;
    font-size: 14px;
    color: #666;
  }

  .tag-modal-input-wrapper {
    position: relative;
    margin-bottom: 20px;
  }

  .tag-modal-input {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    font-family: Arial, sans-serif;
    box-sizing: border-box;
  }

  .tag-modal-input:focus {
    outline: none;
    border-color: #4caf50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
  }

  .tag-modal-input:disabled {
    background-color: #f5f5f5;
    color: #999;
    cursor: not-allowed;
  }

  .tag-modal-suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: white;
    border: 1px solid #ddd;
    border-top: none;
    border-radius: 0 0 4px 4px;
    max-height: 200px;
    overflow-y: auto;
    z-index: 10;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .tag-modal-suggestion-item {
    width: 100%;
    text-align: left;
    padding: 10px 12px;
    border: none;
    background-color: white;
    cursor: pointer;
    font-size: 14px;
    font-family: Arial, sans-serif;
    color: #333;
    transition: background-color 0.15s;
  }

  .tag-modal-suggestion-item:hover:not(:disabled) {
    background-color: #f5f5f5;
  }

  .tag-modal-suggestion-item.selected {
    background-color: #e3f2fd;
    color: #1976d2;
    font-weight: 500;
  }

  .tag-modal-suggestion-item.selected:hover:not(:disabled) {
    background-color: #bbdefb;
  }

  .tag-modal-suggestion-item:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .tag-modal-buttons {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  .tag-modal-cancel-btn {
    padding: 10px 20px;
    background-color: #e0e0e0;
    color: #333;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background-color 0.2s;
  }

  .tag-modal-cancel-btn:hover:not(:disabled) {
    background-color: #d0d0d0;
  }

  .tag-modal-cancel-btn:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .tag-modal-submit-btn {
    padding: 10px 20px;
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background-color 0.2s;
  }

  .tag-modal-submit-btn:hover:not(:disabled) {
    background-color: #45a049;
  }

  .tag-modal-submit-btn:disabled {
    background-color: #999;
    cursor: not-allowed;
  }
</style>
