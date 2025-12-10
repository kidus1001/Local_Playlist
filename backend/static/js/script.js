// static/js/script.js (Revised Logic)

async function startDownload() {
    // ... (All existing variable definitions and input checks remain the same) ...

    const urlInput = document.getElementById('playlistUrl');
    const statusDiv = document.getElementById('statusMessage');
    const downloadButton = document.querySelector('button');
    const playlistUrl = urlInput.value.trim();

    if (!playlistUrl) {
        // ... (Error handling) ...
        return;
    }

    // UI Feedback: Disable button and show pending status
    downloadButton.disabled = true;
    statusDiv.textContent = '⏳ Files are downloading to the server and being packaged... Please wait!';
    statusDiv.className = 'status-box status-pending';

    try {
        // 1. Send the POST request to start the server download (BLOCKING)
        const response = await fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: playlistUrl })
        });

        const data = await response.json();
        downloadButton.disabled = false;

        if (response.ok && data.status === 'success') {
            const downloadId = data.download_id; 
            
            // 2. SUCCESS: Show final confirmation and automatically trigger the browser download
            statusDiv.textContent = '✅ Server download complete! Initiating browser download...';
            statusDiv.className = 'status-box status-success';
            
            // --- AUTOMATIC DOWNLOAD TRIGGER ---
            // This line tells the browser to navigate to the /serve route,
            // which tells the browser to download the ZIP file.
            window.location.href = `/serve/${downloadId}`;
            // ------------------------------------
            
            urlInput.value = ''; // Clear the input field

        } else {
            // ... (Error handling) ...
            statusDiv.innerHTML = `❌ **Download Failed**<br>${data.message || 'Unknown error'}`;
            statusDiv.className = 'status-box status-error';
        }

    } catch (error) {
        // ... (Network error handling) ...
        downloadButton.disabled = false;
        statusDiv.textContent = `❌ Network Error: Could not reach the server.`;
        statusDiv.className = 'status-box status-error';
    }
}