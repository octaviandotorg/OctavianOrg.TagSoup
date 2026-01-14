<script>
  export let imageUrl = '';
  export let imageInfo = null;
  export let onClose = () => {};
  export let onAddTag = () => {};
  export let onDeleteTag = () => {};

  function handleKeydown(event) {
    if (event.key === 'Escape') {
      onClose();
    }
  }

  function handleDownload() {
    // Create a temporary anchor element to trigger download
    const link = document.createElement('a');
    link.href = imageUrl;
    // Modern browsers handle UTF-8 filenames directly
    link.download = imageInfo?.original_filename || 'image';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="full-image-overlay" on:click={onClose}>
  <div class="full-image-container" on:click|stopPropagation>
    <button class="close-btn" on:click={onClose} title="Close (Esc)">
      ✕
    </button>

    <div class="image-wrapper">
      <img src={imageUrl} alt={imageInfo?.original_filename || 'Full size image'} />
    </div>

    <div class="controls-bar">
      <div class="left-controls">
        <div class="image-title">
          {imageInfo?.original_filename || 'Image'}
        </div>
        <button class="download-btn" on:click={handleDownload} title="Download original image">
          ⬇ Download Original
        </button>
      </div>
      <div class="middle-controls">
        {#if imageInfo?.tags && imageInfo.tags.length > 0}
          <div class="tags-list">
            {#each imageInfo.tags as tag (tag)}
              <div class="tag-badge">
                <span>{tag}</span>
                <button
                  class="tag-delete-btn"
                  on:click={() => onDeleteTag(tag)}
                  title="Remove tag"
                  type="button"
                >
                  ×
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
      <button class="tag-btn" on:click={onAddTag}>
        + Tag
      </button>
    </div>
  </div>
</div>

<style>
  .full-image-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.2s ease-in;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .full-image-container {
    position: relative;
    display: flex;
    flex-direction: column;
    width: 90vw;
    height: 90vh;
    background-color: #1a1a1a;
    border-radius: 8px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    overflow: hidden;
  }

  .close-btn {
    position: absolute;
    top: 12px;
    right: 12px;
    background-color: rgba(0, 0, 0, 0.6);
    color: white;
    border: none;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    font-size: 20px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s;
    z-index: 1001;
  }

  .close-btn:hover {
    background-color: rgba(0, 0, 0, 0.9);
  }

  .image-wrapper {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  .image-wrapper img {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  .controls-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    background-color: #2a2a2a;
    border-top: 1px solid #444;
    flex-shrink: 0;
    gap: 16px;
    flex-wrap: wrap;
  }

  .left-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    order: 1;
  }

  .image-title {
    color: white;
    font-size: 14px;
    font-weight: 500;
    word-break: break-word;
  }

  .download-btn {
    background-color: #2196f3;
    color: white;
    border: none;
    padding: 8px 14px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: background-color 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .download-btn:hover {
    background-color: #1976d2;
  }

  .download-btn:focus {
    outline: 2px solid #1565c0;
    outline-offset: 2px;
  }

  .tag-btn {
    background-color: #4caf50;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: background-color 0.2s;
    white-space: nowrap;
    order: 3;
  }

  .tag-btn:hover {
    background-color: #45a049;
  }

  .tag-btn:focus {
    outline: 2px solid #2e7d32;
    outline-offset: 2px;
  }

  .middle-controls {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    min-width: 0;
    order: 2;
  }

  .tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    align-items: center;
  }

  .tag-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    background-color: #4caf50;
    color: white;
    padding: 6px 8px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;
  }

  .tag-badge span {
    padding: 0 4px;
  }

  .tag-delete-btn {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    font-size: 16px;
    padding: 0 4px;
    display: flex;
    align-items: center;
    line-height: 1;
    transition: opacity 0.2s;
  }

  .tag-delete-btn:hover {
    opacity: 0.8;
  }

  .tag-delete-btn:active {
    opacity: 0.6;
  }
</style>
