<script>
  import { createEventDispatcher } from 'svelte';
  import PaginationControls from './PaginationControls.svelte';

  export let images = [];
  export let isLoading = false;
  export let currentPage = 1;
  export let totalPages = 1;

  let hoveredImageId = null;
  const dispatch = createEventDispatcher();

  function onThumbnailHover(imageId) {
    hoveredImageId = imageId;
  }

  function onThumbnailLeave() {
    hoveredImageId = null;
  }

  function onThumbnailClick(image) {
    dispatch('selectImage', image);
  }

  function handlePageChange(pageNum) {
    dispatch('pageChange', pageNum);
  }
</script>

<div class="grid-container">
  {#if isLoading}
    <div class="loading">Loading images...</div>
  {:else if images.length === 0}
    <div class="empty-state">No images found</div>
  {:else}
    <div class="grid-wrapper">
      <div class="grid">
        {#each images as image (image.id)}
          <div
            class="thumbnail-wrapper"
            on:mouseenter={() => onThumbnailHover(image.id)}
            on:mouseleave={onThumbnailLeave}
            on:click={() => onThumbnailClick(image)}
            role="button"
            tabindex="0"
            on:keydown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onThumbnailClick(image);
              }
            }}
          >
            <img src={image.thumbnailUrl} alt={image.original_filename} class="thumbnail" />
            {#if hoveredImageId === image.id}
              <div class="info-overlay">
                <div class="info-content">
                  <p><strong>Filename:</strong> {image.original_filename}</p>
                  <p><strong>Size:</strong> {image.file_size} bytes</p>
                  {#if image.width && image.height}
                    <p><strong>Dimensions:</strong> {image.width}x{image.height}</p>
                  {/if}
                  {#if image.tags && image.tags.length > 0}
                    <p><strong>Tags:</strong> {image.tags.join(', ')}</p>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        {/each}
      </div>
      <div class="pagination-wrapper">
        <PaginationControls
          {currentPage}
          {totalPages}
          onPageChange={handlePageChange}
        />
      </div>
    </div>
  {/if}
</div>

<style>
  .grid-container {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 400px;
  }

  .loading,
  .empty-state {
    font-size: 16px;
    color: #666;
  }

  .grid-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 16px;
    width: 100%;
    flex: 1;
    align-content: start;
    padding: 0;
  }

  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
    padding: 12px 0 0 0;
  }

  .thumbnail-wrapper {
    position: relative;
    aspect-ratio: 1;
    cursor: pointer;
    border-radius: 8px;
    overflow: hidden;
    background-color: #f0f0f0;
    transition: transform 0.2s;
  }

  .thumbnail-wrapper:hover {
    transform: scale(1.02);
  }

  .thumbnail-wrapper:focus {
    outline: 2px solid #4caf50;
    outline-offset: 2px;
  }

  .thumbnail {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: opacity 0.2s;
  }

  .thumbnail-wrapper:hover .thumbnail {
    opacity: 0.7;
  }

  .info-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px;
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

  .info-content {
    color: white;
    font-size: 12px;
    text-align: left;
    width: 100%;
  }

  .info-content p {
    margin: 6px 0;
  }

  .info-content strong {
    font-weight: 600;
  }
</style>
