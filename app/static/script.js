document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const sourcesList = document.getElementById('sources-list');

    // Function to add a message to the chat
    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to display sources
    function displaySources(sources) {
        const sourcesContainer = document.getElementById('sources-list');
        sourcesContainer.innerHTML = '';
        
        if (!sources || sources.length === 0) {
            sourcesContainer.innerHTML = '<p>Inga källor tillgängliga</p>';
            return;
        }

        const sourcesList = document.createElement('ul');
        sourcesList.className = 'sources-list';

        sources.forEach(source => {
            const sourceItem = document.createElement('li');
            sourceItem.className = 'source-item';
            
            const sourceHeader = document.createElement('div');
            sourceHeader.className = 'source-header';
            sourceHeader.innerHTML = `
                <span class="source-file">${source.file}</span>
                <span class="source-relevance">Relevans: ${(source.relevance * 100).toFixed(1)}%</span>
            `;
            
            const sourceText = document.createElement('p');
            sourceText.className = 'source-text';
            sourceText.textContent = source.text;
            
            sourceItem.appendChild(sourceHeader);
            sourceItem.appendChild(sourceText);
            sourcesList.appendChild(sourceItem);
        });

        sourcesContainer.appendChild(sourcesList);
    }

    // Function to send message to API
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, 'user');
        userInput.value = '';

        try {
            // Show loading state
            sendButton.disabled = true;
            sendButton.textContent = 'Skickar...';

            // Send request to API
            const response = await fetch('http://127.0.0.1:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    conversation_history: []  // Add empty conversation history as required by the API
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Add bot response to chat
            addMessage(data.answer, 'bot');

            // Display sources
            if (data.sources) {
                displaySources(data.sources);
            }

        } catch (error) {
            console.error('Error:', error);
            addMessage('Ett fel uppstod. Försök igen senare.', 'system');
        } finally {
            // Reset button state
            sendButton.disabled = false;
            sendButton.textContent = 'Skicka';
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
}); 