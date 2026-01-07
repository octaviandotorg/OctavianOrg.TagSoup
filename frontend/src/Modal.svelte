<script>
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';

  export let isOpen = false;
  export let title = '';
  export let type = 'success'; // 'success' | 'error'

  const dispatch = createEventDispatcher();

  let modalElement;

  function close() {
    dispatch('close');
  }

  function handleKeydown(event) {
    if (event.key === 'Escape' && isOpen) {
      close();
    }
  }

  function handleOverlayClick(event) {
    if (event.target === event.currentTarget) {
      close();
    }
  }

  onMount(() => {
    if (isOpen && modalElement) {
      modalElement.focus();
    }
    document.addEventListener('keydown', handleKeydown);
    return () => {
      document.removeEventListener('keydown', handleKeydown);
    };
  });

  onDestroy(() => {
    document.removeEventListener('keydown', handleKeydown);
  });

  $: if (isOpen && modalElement) {
    modalElement.focus();
  }
</script>

{#if isOpen}
  <div class="modal-overlay" on:click={handleOverlayClick} role="presentation">
    <div
      class="modal-box"
      class:success={type === 'success'}
      class:error={type === 'error'}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      bind:this={modalElement}
      tabindex="-1"
    >
      <div class="modal-header">
        <h2 id="modal-title">{title}</h2>
        <button class="close-btn" on:click={close} aria-label="Close dialog">
          &times;
        </button>
      </div>
      <div class="modal-content">
        <slot></slot>
      </div>
      <div class="modal-footer">
        <button class="close-action-btn" on:click={close}>Close</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    animation: fadeIn 0.3s ease-in-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .modal-box {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    max-width: 600px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    animation: slideIn 0.3s ease-in-out;
  }

  @keyframes slideIn {
    from {
      transform: translateY(-50px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #eee;
  }

  .modal-header h2 {
    margin: 0;
    font-size: 20px;
    color: #333;
  }

  .modal-box.success .modal-header h2 {
    color: #4caf50;
  }

  .modal-box.error .modal-header h2 {
    color: #f44336;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 28px;
    cursor: pointer;
    color: #666;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: background-color 0.2s;
  }

  .close-btn:hover {
    background-color: #f0f0f0;
  }

  .close-btn:focus {
    outline: 2px solid #4caf50;
    outline-offset: 2px;
  }

  .modal-content {
    padding: 20px;
    color: #333;
    line-height: 1.6;
  }

  .modal-content :global(pre) {
    background-color: #f5f5f5;
    padding: 12px;
    border-radius: 4px;
    border-left: 4px solid #4caf50;
    overflow-x: auto;
    font-size: 13px;
    line-height: 1.5;
  }

  .modal-box.error .modal-content :global(pre) {
    border-left-color: #f44336;
    background-color: #fef5f5;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    padding: 15px 20px;
    border-top: 1px solid #eee;
    gap: 10px;
  }

  .close-action-btn {
    background-color: #4caf50;
    color: white;
    padding: 10px 24px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background-color 0.2s;
  }

  .modal-box.error .close-action-btn {
    background-color: #f44336;
  }

  .close-action-btn:hover {
    background-color: #45a049;
  }

  .modal-box.error .close-action-btn:hover {
    background-color: #d32f2f;
  }

  .close-action-btn:focus {
    outline: 2px solid #2e7d32;
    outline-offset: 2px;
  }
</style>
