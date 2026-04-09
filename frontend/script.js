document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const clearBtn = document.getElementById('clear-btn');
    
    // Original welcome message
    const initialWelcomeMessage = chatMessages.innerHTML;
    
    // Fetch and load chat history
    async function loadHistory() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            if (data.length > 0) {
                // Clear initial welcome message if there is history
                chatMessages.innerHTML = '';
                data.forEach(msg => {
                    chatMessages.appendChild(createMessageElement(msg.text, msg.sender === 'user'));
                });
                scrollToBottom();
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    function createMessageElement(text, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const textP = document.createElement('p');
        textP.textContent = text;
        
        contentDiv.appendChild(textP);
        messageDiv.appendChild(contentDiv);
        
        return messageDiv;
    }

    function createTypingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message typing-indicator-msg';
        messageDiv.id = 'typing-indicator';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            contentDiv.appendChild(dot);
        }
        
        messageDiv.appendChild(contentDiv);
        return messageDiv;
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function handleSendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // Clear input
        chatInput.value = '';

        // Add user message to UI
        chatMessages.appendChild(createMessageElement(text, true));
        scrollToBottom();

        // Add typing indicator
        const typingIndicator = createTypingIndicator();
        chatMessages.appendChild(typingIndicator);
        scrollToBottom();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: text }),
            });

            const data = await response.json();
            
            // Remove typing indicator
            const indicator = document.getElementById('typing-indicator');
            if (indicator) indicator.remove();

            // Add bot response
            chatMessages.appendChild(createMessageElement(data.response, false));
            scrollToBottom();

        } catch (error) {
            console.error('Error fetching response:', error);
            const indicator = document.getElementById('typing-indicator');
            if (indicator) indicator.remove();
            
            chatMessages.appendChild(createMessageElement('Sorry, I encountered an error connecting to the server.', false));
            scrollToBottom();
        }
    }

    sendBtn.addEventListener('click', handleSendMessage);

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    });

    // Clear Chat functionality
    clearBtn.addEventListener('click', async () => {
        try {
            await fetch('/api/history', { method: 'DELETE' });
            chatMessages.innerHTML = initialWelcomeMessage;
            chatInput.value = '';
            chatInput.focus();
        } catch (error) {
            console.error('Failed to clear history:', error);
        }
    });

    // Initial focus and load
    chatInput.focus();
    loadHistory();
});
