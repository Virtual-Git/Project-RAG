// Wait for the DOM to be fully loaded before running script
document.addEventListener('DOMContentLoaded', () => {

    // --- Get DOM Elements ---
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const toggleBtn = document.getElementById('toggle-btn');
    const closeBtn = document.getElementById('close-btn');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatContainer = document.getElementById('chat-container');
    const restartBtn = document.getElementById('restart-btn');

    // --- Sidebar Toggle Functions ---
    function openNav() {
        sidebar.style.width = '250px';
        mainContent.style.marginLeft = '250px';
    }

    function closeNav() {
        sidebar.style.width = '0';
        mainContent.style.marginLeft = '0';
    }

    // --- Event Listeners ---
    toggleBtn.addEventListener('click', openNav);
    closeBtn.addEventListener('click', closeNav);
    chatForm.addEventListener('submit', handleChatSubmit);
    restartBtn.addEventListener('click', handleRestart);

    /**
     * Handles the chat form submission.
     * @param {Event} e - The form submission event.
     */
    async function handleChatSubmit(e) {
        e.preventDefault(); // Prevent default page reload
        const query = chatInput.value.trim();

        if (!query) return; // Don't send empty messages

        // 1. Display the user's message
        addMessageToChat('user', query);

        // 2. Clear the input field
        chatInput.value = '';

        // 3. Display a "thinking" message from the bot
        const thinkingMsgElement = addMessageToChat('bot', '...', true);

        try {
            // 4. Send the query to the Flask backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query }),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || `HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();

            // 5. Update the "thinking" message with the actual response
            updateBotMessage(thinkingMsgElement, data.response);

        } catch (error) {
            console.error('Error during chat:', error);
            // 5b. Update the "thinking" message with an error
            updateBotMessage(thinkingMsgElement, `Error: ${error.message}`, true);
        }
    }

    /**
     * Handles the restart button click.
     */
    async function handleRestart() {
        try {
            await fetch('/restart', { method: 'POST' });
            // Clear all messages except the first welcome message
            chatContainer.innerHTML = `
                <div class="chat-message bot-msg">
                    <p>Hello! Ask me any questions about the loaded books.</p>
                </div>`;
            console.log('Chat history cleared.');
        } catch (error) {
            console.error('Error restarting chat:', error);
        }
    }

    /**
     * Adds a new message to the chat window.
     * @param {'user' | 'bot'} role - The sender of the message.
     * @param {string} content - The text content of the message.
     * @param {boolean} [isThinking=false] - If true, style as a "thinking" message.
     * @returns {HTMLElement} The created message element.
     */
    function addMessageToChat(role, content, isThinking = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${role}-msg`;
        
        if (isThinking) {
            msgDiv.classList.add('thinking');
        }

        // Use <p> tag to respect newlines from the bot
        const p = document.createElement('p');
        p.textContent = content; // Safely sets text content
        msgDiv.appendChild(p);

        chatContainer.appendChild(msgDiv);
        
        // Auto-scroll to the bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;

        return msgDiv;
    }

    /**
     * Updates an existing bot message (typically a "thinking" message).
     * @param {HTMLElement} msgElement - The message element to update.
     * @param {string} newContent - The new text content.
     * @param {boolean} [isError=false] - If true, style as an error.
     */
    function updateBotMessage(msgElement, newContent, isError = false) {
        msgElement.classList.remove('thinking');
        if (isError) {
            msgElement.classList.add('error');
        }
        
        // Find the <p> tag inside and update its content
        const p = msgElement.querySelector('p');
        if (p) {
            p.textContent = newContent;
        }

        // Auto-scroll again in case the new content is long
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // --- Initial Sidebar State ---
    // Start with the sidebar open by default
    openNav();
});

// Wait for the DOM to be fully loaded before running script
document.addEventListener('DOMContentLoaded', () => {

    // --- Get DOM Elements ---
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const toggleBtn = document.getElementById('toggle-btn');
    const closeBtn = document.getElementById('close-btn');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatContainer = document.getElementById('chat-container');
    const restartBtn = document.getElementById('restart-btn');

    // --- ADDED: Upload Form Elements ---
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const uploadButton = document.getElementById('upload-button');
    const fileList = document.getElementById('file-list');
    // --- END ADDED ---

    // --- Sidebar Toggle Functions ---
    function openNav() {
        sidebar.style.width = '250px';
        mainContent.style.marginLeft = '250px';
    }

    function closeNav() {
        sidebar.style.width = '0';
        mainContent.style.marginLeft = '0';
    }

    // --- Event Listeners ---
    toggleBtn.addEventListener('click', openNav);
    closeBtn.addEventListener('click', closeNav);
    chatForm.addEventListener('submit', handleChatSubmit);
    restartBtn.addEventListener('click', handleRestart);
    uploadForm.addEventListener('submit', handleUploadSubmit); // <-- ADDED

    /**
     * Handles the chat form submission.
     * @param {Event} e - The form submission event.
     */
    async function handleChatSubmit(e) {
        e.preventDefault(); 
        const query = chatInput.value.trim();
        if (!query) return; 
        addMessageToChat('user', query);
        chatInput.value = '';
        const thinkingMsgElement = addMessageToChat('bot', '...', true);

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query }),
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || `HTTP error! Status: ${response.status}`);
            }
            const data = await response.json();
            updateBotMessage(thinkingMsgElement, data.response);

        } catch (error) {
            console.error('Error during chat:', error);
            updateBotMessage(thinkingMsgElement, `Error: ${error.message}`, true);
        }
    }

    /**
     * Handles the restart button click.
     */
    async function handleRestart() {
        try {
            await fetch('/restart', { method: 'POST' });
            chatContainer.innerHTML = `
                <div class="chat-message bot-msg">
                    <p>Hello! Ask me any questions about the loaded books.</p>
                </div>`;
            console.log('Chat history cleared.');
        } catch (error) {
            console.error('Error restarting chat:', error);
        }
    }

    // --- NEW: Handle File Upload ---
    /**
     * Handles the file upload form submission.
     * @param {Event} e - The form submission event.
     */
    async function handleUploadSubmit(e) {
        e.preventDefault();
        const file = fileInput.files[0];
        
        if (!file) {
            setUploadStatus('Please select a file.', 'error');
            return;
        }

        // Create form data
        const formData = new FormData();
        formData.append('file', file);

        // Disable button and set status
        uploadButton.disabled = true;
        setUploadStatus('Uploading and indexing...', 'thinking');

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData, // No 'Content-Type' header needed; browser sets it
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! Status: ${response.status}`);
            }

            // Success!
            setUploadStatus(data.message, 'success');
            // Add new file to the sidebar list
            addFileToSidebar(data.filename);
            // Clear the file input
            uploadForm.reset(); 

        } catch (error) {
            console.error('Error during upload:', error);
            setUploadStatus(error.message, 'error');
        } finally {
            // Re-enable the button
            uploadButton.disabled = false;
        }
    }

    /**
     * Sets the text and style for the upload status message.
     * @param {string} message - The message to display.
     * @param {'success' | 'error' | 'thinking'} type - The message type for styling.
     */
    function setUploadStatus(message, type) {
        uploadStatus.textContent = message;
        uploadStatus.className = type; // 'success', 'error', or 'thinking'
    }

    /**
     * Dynamically adds a new file name to the sidebar list.
     * @param {string} filename - The name of the file to add.
     */
    function addFileToSidebar(filename) {
        // Remove the "No .md files found" placeholder if it exists
        const placeholder = document.getElementById('no-files-placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        const li = document.createElement('li');
        li.textContent = filename;
        fileList.appendChild(li);
    }
    // --- END NEW FUNCTIONS ---


    /**
     * Adds a new message to the chat window.
     * @param {'user' | 'bot'} role - The sender of the message.
     * @param {string} content - The text content of the message.
     * @param {boolean} [isThinking=false] - If true, style as a "thinking" message.
     * @returns {HTMLElement} The created message element.
     */
    function addMessageToChat(role, content, isThinking = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${role}-msg`;
        if (isThinking) {
            msgDiv.classList.add('thinking');
        }
        const p = document.createElement('p');
        p.textContent = content; 
        msgDiv.appendChild(p);
        chatContainer.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return msgDiv;
    }

    /**
     * Updates an existing bot message (typically a "thinking" message).
     * @param {HTMLElement} msgElement - The message element to update.
     * @param {string} newContent - The new text content.
     * @param {boolean} [isError=false] - If true, style as an error.
     */
    function updateBotMessage(msgElement, newContent, isError = false) {
        msgElement.classList.remove('thinking');
        if (isError) {
            msgElement.classList.add('error');
        }
        const p = msgElement.querySelector('p');
        if (p) {
            p.textContent = newContent;
        }
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // --- Initial Sidebar State ---
    openNav();
});