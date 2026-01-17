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
  let selectedImageIds = new Set();
  let showBulkTagModal = false;
  let bulkTagInputValue = '';
  let isBulkTagging = false;
  let bulkTagSuggestions = [];
  let selectedBulkSuggestionIndex = -1;

  // Upload queue state
  let uploadQueue = []; // {id, file, status: 'pending'|'uploading'|'success'|'error', error}
  let showUploadProgressModal = false;
  let isUploadingBatch = false;
  let uploadedCount = 0;
  let totalToUpload = 0;
  const MAX_CONCURRENT_UPLOADS = 3;

  $: images = pages[currentPage - 1]?.images || [];
  $: totalPages = pages.length;
  $: hasSelectedImages = selectedImageIds.size > 0;
  $: isAllSelected = images.length > 0 && images.every(img => selectedImageIds.has(img.id));

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
      const data = await getImagesInfo(50, cursor, tags);
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
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    uploadQueue = files.map((file, index) => ({
      id: `${Date.now()}-${index}`,
      file,
      status: 'pending',
      error: null,
    }));

    totalToUpload = files.length;
    uploadedCount = 0;
    showUploadProgressModal = true;
    handleBatchUpload();
  }

  async function handleUpload() {
    if (!selectedFile) return;

    isUploading = true;
    try {
      const data = await uploadImage(selectedFile);

      // Reload images after successful upload
      await loadImages();

      // Clear file input after successful upload
      selectedFile = null;
      fileInput.value = '';
    } catch (error) {
      modalType = 'error';
      modalTitle = 'Upload Failed';
      modalData = { detail: error.message };
      showModal = true;
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

  async function handleBatchUpload() {
    isUploadingBatch = true;

    try {
      await uploadFilesWithConcurrency(uploadQueue, MAX_CONCURRENT_UPLOADS);
      await loadImages(selectedTags);
      fileInput.value = '';
    } finally {
      isUploadingBatch = false;
    }
  }

  async function uploadFilesWithConcurrency(queue, maxConcurrent) {
    const pending = [...queue];
    const executing = [];

    for (const item of pending) {
      const promise = uploadSingleFile(item).then(() => {
        executing.splice(executing.indexOf(promise), 1);
      });
      executing.push(promise);

      if (executing.length >= maxConcurrent) {
        await Promise.race(executing);
      }
    }
    await Promise.all(executing);
  }

  async function uploadSingleFile(uploadItem) {
    uploadItem.status = 'uploading';
    uploadQueue = [...uploadQueue];

    try {
      await uploadImage(uploadItem.file);
      uploadItem.status = 'success';
      uploadedCount++;
    } catch (error) {
      uploadItem.status = 'error';
      uploadItem.error = error.message;
    }
    uploadQueue = [...uploadQueue];
  }

  function closeUploadProgressModal() {
    showUploadProgressModal = false;
    uploadQueue = [];
    uploadedCount = 0;
    totalToUpload = 0;
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

  function handleToggleSelect(event) {
    const imageId = event.detail;
    const newSet = new Set(selectedImageIds);
    if (newSet.has(imageId)) {
      newSet.delete(imageId);
    } else {
      newSet.add(imageId);
    }
    selectedImageIds = newSet;
  }

  function handleSelectAll() {
    const newSet = new Set(selectedImageIds);
    const allCurrentIds = images.map(img => img.id);
    const allSelected = allCurrentIds.every(id => newSet.has(id));

    if (allSelected) {
      // Deselect all on current page
      allCurrentIds.forEach(id => newSet.delete(id));
    } else {
      // Select all on current page
      allCurrentIds.forEach(id => newSet.add(id));
    }
    selectedImageIds = newSet;
  }

  function handleClearSelection() {
    selectedImageIds = new Set();
  }

  function handleBulkTag() {
    showBulkTagModal = true;
    bulkTagInputValue = '';
    bulkTagSuggestions = [];
    selectedBulkSuggestionIndex = -1;
  }

  function closeBulkTagModal() {
    showBulkTagModal = false;
    bulkTagInputValue = '';
    bulkTagSuggestions = [];
    selectedBulkSuggestionIndex = -1;
  }

  function searchBulkTagSuggestions(value) {
    if (!value || !tagTree) {
      bulkTagSuggestions = [];
      selectedBulkSuggestionIndex = -1;
      return;
    }

    const results = tagTree.search(value.toLowerCase(), { limit: 5 });
    const uniqueTags = new Set();
    for (const result of results.matches) {
      uniqueTags.add(result.stringId);
    }
    bulkTagSuggestions = Array.from(uniqueTags);
    selectedBulkSuggestionIndex = -1;
  }

  function selectBulkSuggestedTag(tag) {
    bulkTagInputValue = tag;
    bulkTagSuggestions = [];
    selectedBulkSuggestionIndex = -1;
  }

  function handleBulkTagKeydown(event) {
    if (event.key === 'Escape') {
      closeBulkTagModal();
    } else if (event.key === 'Enter') {
      event.preventDefault();
      if (selectedBulkSuggestionIndex >= 0 && bulkTagSuggestions[selectedBulkSuggestionIndex]) {
        selectBulkSuggestedTag(bulkTagSuggestions[selectedBulkSuggestionIndex]);
      } else {
        submitBulkTag();
      }
    } else if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (bulkTagSuggestions.length > 0) {
        selectedBulkSuggestionIndex = Math.min(
          selectedBulkSuggestionIndex + 1,
          bulkTagSuggestions.length - 1
        );
      }
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      if (selectedBulkSuggestionIndex > 0) {
        selectedBulkSuggestionIndex--;
      }
    }
  }

  async function submitBulkTag() {
    const tag = bulkTagInputValue.trim();
    if (!tag) return;

    isBulkTagging = true;
    const imageIds = Array.from(selectedImageIds);

    try {
      // Apply tag to all selected images in parallel
      await Promise.all(imageIds.map(id => addImageTag(id, tag)));

      // Update local state for all pages
      pages = pages.map(page => ({
        ...page,
        images: page.images.map(img => {
          if (selectedImageIds.has(img.id)) {
            return {
              ...img,
              tags: img.tags.includes(tag) ? img.tags : [...img.tags, tag]
            };
          }
          return img;
        })
      }));

      // Update full image view if it's one of the tagged images
      if (selectedImageForDisplay && selectedImageIds.has(selectedImageForDisplay.id)) {
        selectedImageForDisplay = {
          ...selectedImageForDisplay,
          tags: selectedImageForDisplay.tags.includes(tag)
            ? selectedImageForDisplay.tags
            : [...selectedImageForDisplay.tags, tag]
        };
      }

      // Update global tags list
      if (!allTags.includes(tag)) {
        allTags = [...allTags, tag];
        if (tagTree) {
          tagTree.addString(tag.toLowerCase(), tag);
        }
      }

      // Clear selection and close modal
      selectedImageIds = new Set();
      closeBulkTagModal();
    } catch (error) {
      modalType = 'error';
      modalTitle = 'Bulk Tag Failed';
      modalData = { detail: error.message };
      showModal = true;
    } finally {
      isBulkTagging = false;
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
    <div class="header-tag-input-wrapper">
      <input
        type="text"
        placeholder="Filter tags..."
        bind:value={tagInput}
        on:keydown={handleTagInputKeydown}
        on:input={(e) => searchTagSuggestions(e.target.value)}
        class="header-tag-input"
      />
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
    <div class="header-controls">
      {#if images.length > 0}
        <label class="select-all-container">
          <input
            type="checkbox"
            checked={isAllSelected}
            on:change={handleSelectAll}
          />
          Select All
        </label>
      {/if}
      <div class="upload-button-container">
        {#if hasSelectedImages}
          <button on:click={handleClearSelection} class="clear-selection-btn">
            Clear Selection
          </button>
          <button on:click={handleBulkTag} class="bulk-tag-btn">
            + Tag ({selectedImageIds.size})
          </button>
        {/if}
        <input
          type="file"
          accept="image/*"
          multiple
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
    </div>
  </header>

  <main class="main-content">
    {#if selectedTags.length > 0}
      <div class="tag-section">
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
      </div>
    {/if}

    <ThumbnailGrid
      {images}
      {currentPage}
      {totalPages}
      {selectedImageIds}
      isLoading={isLoadingImages}
      on:selectImage={handleSelectImage}
      on:toggleSelect={handleToggleSelect}
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

{#if showBulkTagModal}
  <div class="tag-modal-overlay" on:click={closeBulkTagModal}>
    <div class="tag-modal-content" on:click|stopPropagation>
      <h2>Add Tag to {selectedImageIds.size} Images</h2>
      <p>Enter a tag to apply to all selected images</p>
      <div class="tag-modal-input-wrapper">
        <input
          type="text"
          placeholder="Enter tag name..."
          bind:value={bulkTagInputValue}
          on:keydown={handleBulkTagKeydown}
          on:input={(e) => searchBulkTagSuggestions(e.target.value)}
          autoFocus
          disabled={isBulkTagging}
          class="tag-modal-input"
        />
        {#if bulkTagSuggestions.length > 0}
          <div class="tag-modal-suggestions">
            {#each bulkTagSuggestions as suggestion, index (suggestion)}
              <button
                class="tag-modal-suggestion-item"
                class:selected={index === selectedBulkSuggestionIndex}
                on:click={() => selectBulkSuggestedTag(suggestion)}
                type="button"
                disabled={isBulkTagging}
              >
                {suggestion}
              </button>
            {/each}
          </div>
        {/if}
      </div>
      <div class="tag-modal-buttons">
        <button
          on:click={closeBulkTagModal}
          disabled={isBulkTagging}
          class="tag-modal-cancel-btn"
        >
          Cancel
        </button>
        <button
          on:click={submitBulkTag}
          disabled={isBulkTagging || !bulkTagInputValue.trim()}
          class="tag-modal-submit-btn"
        >
          {isBulkTagging ? 'Adding...' : 'Add Tag to All'}
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showUploadProgressModal}
  <div class="upload-modal-overlay" on:click={(e) => { if (!isUploadingBatch) closeUploadProgressModal(); }}>
    <div class="upload-modal-content" on:click|stopPropagation>
      <h2>Uploading Images</h2>
      <p>{uploadedCount} of {totalToUpload} complete</p>

      <div class="upload-progress-bar">
        <div class="upload-progress-fill" style="width: {(uploadedCount / totalToUpload) * 100}%"></div>
      </div>

      <div class="upload-file-list">
        {#each uploadQueue as item (item.id)}
          <div class="upload-file-item" class:success={item.status === 'success'} class:error={item.status === 'error'}>
            <span class="file-name">{item.file.name}</span>
            <span class="file-status">
              {#if item.status === 'pending'}
                <span class="status-pending">Waiting...</span>
              {:else if item.status === 'uploading'}
                <span class="status-uploading">Uploading...</span>
              {:else if item.status === 'success'}
                <span class="status-success">✓ Success</span>
              {:else if item.status === 'error'}
                <span class="status-error">✗ {item.error}</span>
              {/if}
            </span>
          </div>
        {/each}
      </div>

      <div class="upload-modal-buttons">
        <button on:click={closeUploadProgressModal} disabled={isUploadingBatch} class="upload-modal-close-btn">
          {isUploadingBatch ? 'Uploading...' : 'Close'}
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
    flex: 0 0 auto;
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

  .header-tag-input-wrapper {
    position: relative;
    width: 350px;
    margin: 0 20px 0 20px;
  }

  .header-tag-input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    font-family: Arial, sans-serif;
  }

  .header-tag-input:focus {
    outline: none;
    border-color: #4caf50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
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
    margin-bottom: 12px;
    padding: 0;
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

  .header-controls {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .select-all-container {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    cursor: pointer;
    user-select: none;
  }

  .select-all-container input[type="checkbox"] {
    cursor: pointer;
  }

  .bulk-tag-btn {
    background-color: #2196f3;
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

  .bulk-tag-btn:hover {
    background-color: #1976d2;
  }

  .bulk-tag-btn:focus {
    outline: 2px solid #1565c0;
    outline-offset: 2px;
  }

  .clear-selection-btn {
    background-color: #757575;
    color: white;
    padding: 10px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background-color 0.2s;
    white-space: nowrap;
  }

  .clear-selection-btn:hover {
    background-color: #616161;
  }

  .clear-selection-btn:focus {
    outline: 2px solid #424242;
    outline-offset: 2px;
  }

  .upload-modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1002;
  }

  .upload-modal-content {
    background-color: white;
    border-radius: 8px;
    padding: 28px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    max-width: 600px;
    width: 90%;
    max-height: 70vh;
    display: flex;
    flex-direction: column;
    animation: slideUp 0.2s ease-out;
  }

  .upload-modal-content h2 {
    margin: 0 0 8px 0;
    font-size: 18px;
    color: #333;
    font-weight: 600;
  }

  .upload-modal-content p {
    margin: 0 0 16px 0;
    font-size: 14px;
    color: #666;
  }

  .upload-progress-bar {
    width: 100%;
    height: 24px;
    background-color: #e0e0e0;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 20px;
  }

  .upload-progress-fill {
    height: 100%;
    background-color: #4caf50;
    transition: width 0.3s ease;
  }

  .upload-file-list {
    flex: 1;
    overflow-y: auto;
    margin-bottom: 20px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 12px;
    max-height: 300px;
  }

  .upload-file-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    margin-bottom: 8px;
    border-radius: 4px;
    background-color: #f5f5f5;
    transition: background-color 0.2s;
  }

  .upload-file-item:last-child {
    margin-bottom: 0;
  }

  .upload-file-item.success {
    background-color: #e8f5e9;
  }

  .upload-file-item.error {
    background-color: #ffebee;
  }

  .file-name {
    font-size: 14px;
    color: #333;
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-right: 12px;
  }

  .file-status {
    font-size: 13px;
    white-space: nowrap;
  }

  .status-pending {
    color: #757575;
  }

  .status-uploading {
    color: #2196f3;
    font-weight: 500;
  }

  .status-success {
    color: #4caf50;
    font-weight: 500;
  }

  .status-error {
    color: #f44336;
    font-size: 12px;
  }

  .upload-modal-buttons {
    display: flex;
    justify-content: flex-end;
  }

  .upload-modal-close-btn {
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

  .upload-modal-close-btn:hover:not(:disabled) {
    background-color: #45a049;
  }

  .upload-modal-close-btn:disabled {
    background-color: #999;
    cursor: not-allowed;
  }
</style>
