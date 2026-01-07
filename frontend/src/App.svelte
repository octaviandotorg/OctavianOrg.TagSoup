<script>
  import Modal from './Modal.svelte';

  let greeting = 'Welcome to TagSoup';
  let selectedFile = null;
  let isUploading = false;
  let showModal = false;
  let modalData = null;
  let modalType = 'success';
  let modalTitle = '';
  let fileInput;

  function handleFileSelect(event) {
    selectedFile = event.target.files[0] || null;
  }

  async function handleUpload() {
    if (!selectedFile) return;

    isUploading = true;
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/image/uploadImage', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        modalType = 'success';
        modalTitle = 'Upload Successful';
        modalData = data;
      } else {
        modalType = 'error';
        modalTitle = 'Upload Failed';
        modalData = data;
      }
    } catch (error) {
      modalType = 'error';
      modalTitle = 'Upload Failed';
      modalData = { detail: `Network error: ${error.message}` };
    } finally {
      isUploading = false;
      showModal = true;
    }
  }

  function closeModal() {
    showModal = false;
    if (modalType === 'success') {
      selectedFile = null;
      fileInput.value = '';
    }
  }
</script>

<main>
  <h1>{greeting}</h1>
  <p>Image management and tagging application</p>

  <div class="upload-section">
    <h2>Upload Image</h2>
    <div class="upload-controls">
      <input
        type="file"
        accept="image/*"
        on:change={handleFileSelect}
        bind:this={fileInput}
        id="file-input"
      />
      <button
        on:click={handleUpload}
        disabled={!selectedFile || isUploading}
        class="upload-btn"
      >
        {isUploading ? 'Uploading...' : 'Upload'}
      </button>
    </div>
    {#if selectedFile}
      <p class="selected-file">Selected: {selectedFile.name}</p>
    {/if}
  </div>
</main>

<Modal
  isOpen={showModal}
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
  }

  main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }

  h1 {
    color: #333;
  }

  p {
    color: #666;
  }

  .upload-section {
    margin-top: 40px;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
    background-color: #fafafa;
  }

  .upload-section h2 {
    margin-top: 0;
    margin-bottom: 16px;
    color: #333;
    font-size: 18px;
  }

  .upload-controls {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }

  input[type='file'] {
    flex: 1;
    min-width: 200px;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 14px;
  }

  input[type='file']:focus {
    outline: 2px solid #4caf50;
    outline-offset: 2px;
  }

  .upload-btn {
    background-color: #4caf50;
    color: white;
    padding: 10px 24px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background-color 0.2s;
    white-space: nowrap;
  }

  .upload-btn:hover:not(:disabled) {
    background-color: #45a049;
  }

  .upload-btn:focus {
    outline: 2px solid #2e7d32;
    outline-offset: 2px;
  }

  .upload-btn:disabled {
    background-color: #ccc;
    cursor: not-allowed;
    opacity: 0.6;
  }

  .selected-file {
    margin-top: 12px;
    font-size: 13px;
    color: #666;
  }
</style>
