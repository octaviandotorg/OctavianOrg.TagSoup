<script>
  export let currentPage = 1;
  export let totalPages = 1;
  export let maxVisiblePages = 5;
  export let onPageChange = () => {};

  let visibleStartPage = 1;

  $: {
    // Adjust visible range when current page is out of view
    if (currentPage < visibleStartPage) {
      visibleStartPage = currentPage;
    } else if (currentPage > visibleStartPage + maxVisiblePages - 1) {
      visibleStartPage = currentPage - maxVisiblePages + 1;
    }
  }

  $: visibleEndPage = Math.min(visibleStartPage + maxVisiblePages - 1, totalPages);
  $: visiblePages = Array.from(
    { length: visibleEndPage - visibleStartPage + 1 },
    (_, i) => visibleStartPage + i
  );
  $: showLeftArrow = visibleStartPage > 1;
  $: showRightArrow = visibleEndPage < totalPages;

  function goToPage(pageNum) {
    if (pageNum >= 1 && pageNum <= totalPages && pageNum !== currentPage) {
      onPageChange(pageNum);
    }
  }

  function scrollLeft() {
    visibleStartPage = Math.max(1, visibleStartPage - maxVisiblePages);
  }

  function scrollRight() {
    visibleStartPage = Math.min(totalPages - maxVisiblePages + 1, visibleStartPage + maxVisiblePages);
  }
</script>

<div class="pagination-container">
  {#if totalPages > 1}
    <div class="pagination-controls">
      {#if showLeftArrow}
        <button class="arrow-btn" on:click={scrollLeft} title="Previous pages">
          ◀
        </button>
      {/if}

      <div class="page-buttons">
        {#each visiblePages as pageNum (pageNum)}
          <button
            class="page-btn"
            class:active={pageNum === currentPage}
            on:click={() => goToPage(pageNum)}
          >
            {pageNum}
          </button>
        {/each}
      </div>

      {#if showRightArrow}
        <button class="arrow-btn" on:click={scrollRight} title="Next pages">
          ▶
        </button>
      {/if}
    </div>
  {/if}
</div>

<style>
  .pagination-container {
    display: flex;
    justify-content: flex-end;
    padding: 0;
  }

  .pagination-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    background-color: white;
    padding: 8px 12px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .page-buttons {
    display: flex;
    gap: 4px;
  }

  .page-btn {
    min-width: 36px;
    height: 36px;
    padding: 0;
    background-color: #f5f5f5;
    color: #333;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s;
  }

  .page-btn:hover {
    background-color: #e8f5e9;
    border-color: #4caf50;
    color: #2e7d32;
  }

  .page-btn.active {
    background-color: #4caf50;
    color: white;
    border-color: #4caf50;
  }

  .page-btn:focus {
    outline: 2px solid #2e7d32;
    outline-offset: 2px;
  }

  .arrow-btn {
    width: 36px;
    height: 36px;
    padding: 0;
    background-color: #f5f5f5;
    color: #666;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .arrow-btn:hover {
    background-color: #4caf50;
    color: white;
    border-color: #4caf50;
  }

  .arrow-btn:focus {
    outline: 2px solid #2e7d32;
    outline-offset: 2px;
  }
</style>
