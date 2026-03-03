// YouTube Learning Assistant - Frontend JavaScript
console.log('🚀 App started');

const API = 'http://localhost:8000/api';
let state = {
    videoId: null,
    sessionId: 'session_' + Date.now(),
    isProcessing: false
};

// DOM Elements
const messagesDiv = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// Initialize
function init() {
    console.log('🎬 Initializing app...');
    
    // Add welcome message
    addBotMessage('👋 Hi! I\'m your YouTube Learning Assistant.\n\nPaste a YouTube video URL to get started, and I\'ll help you learn from it!');
    
    // Setup event listeners
    sendBtn.addEventListener('click', handleSend);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !state.isProcessing) {
            handleSend();
        }
    });
    
    console.log('✅ App initialized');
}

async function handleSend() {
    const input = userInput.value.trim();
    if (!input || state.isProcessing) return;

    const isYouTubeUrl = input.includes('youtube.com') || input.includes('youtu.be');

    if (!state.videoId && isYouTubeUrl) {
        await processVideo(input);
    } else if (state.videoId) {
        await askQuestion(input);
    } else {
        addBotMessage('⚠️ Please paste a valid YouTube URL first.');
    }
}

async function processVideo(url) {
    console.log('📹 Processing video:', url);
    state.isProcessing = true;
    userInput.value = '';
    userInput.disabled = true;
    sendBtn.disabled = true;

    addUserMessage(url);
    const loadingId = addBotMessage('🔄 Processing video... This may take 30-60 seconds.', true);

    try {
        const res = await fetch(API + '/ingest/video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        const data = await res.json();
        removeMessage(loadingId);

        if (res.ok) {
            state.videoId = data.video_id;
            console.log('✅ Video ID saved:', state.videoId);
            
            addVideoPlayer(state.videoId);
            addBotMessage(
                `✅ Video loaded successfully!\n\n` +
                `📊 Duration: ${data.duration}\n` +
                `📝 Segments: ${data.total_segments}\n\n` +
                `Now you can ask me anything about this video!`
            );
            
            userInput.placeholder = 'Ask anything about this video...';
        } else {
            const errorMsg = data.detail?.message || 'Failed to load video';
            addBotMessage(`❌ Error: ${errorMsg}\n\n💡 Make sure the video has captions/subtitles enabled.`);
        }
    } catch (err) {
        console.error('❌ Error:', err);
        removeMessage(loadingId);
        addBotMessage(`❌ Network error: ${err.message}`);
    }

    state.isProcessing = false;
    userInput.disabled = false;
    sendBtn.disabled = false;
    userInput.focus();
}

async function askQuestion(question) {
    state.isProcessing = true;
    userInput.value = '';
    userInput.disabled = true;
    sendBtn.disabled = true;

    addUserMessage(question);
    const loadingId = addBotMessage('', true, true);

    try {
        const res = await fetch(API + '/chat/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                video_id: state.videoId, 
                question: question,
                session_id: state.sessionId 
            })
        });

        const data = await res.json();
        removeMessage(loadingId);

        if (res.ok) {
            addBotMessage(data.answer);
            if (data.sources && data.sources.length > 0) {
                addSources(data.sources);
            }
        } else {
            const errorMsg = data.detail?.message || 'Failed to get answer';
            addBotMessage(`❌ Error: ${errorMsg}`);
        }
    } catch (err) {
        console.error('❌ Error:', err);
        removeMessage(loadingId);
        addBotMessage(`❌ Network error: ${err.message}`);
    }

    state.isProcessing = false;
    userInput.disabled = false;
    sendBtn.disabled = false;
    userInput.focus();
}

function addUserMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user';
    msgDiv.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-content">${escapeHtml(text)}</div>
    `;
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
}

function addBotMessage(text, isLoading = false, isTyping = false) {
    const msgId = 'msg_' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.id = msgId;
    msgDiv.className = 'message bot';
    
    if (isTyping) {
        msgDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
    } else if (isLoading) {
        msgDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content loading-message">${text}</div>
        `;
    } else {
        msgDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">${escapeHtml(text)}</div>
        `;
    }
    
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
    return msgId;
}

function addVideoPlayer(videoId) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot';
    msgDiv.innerHTML = `
        <div class="message-avatar">🎥</div>
        <div class="message-content" style="max-width: 100%;">
            <div class="video-player">
                <iframe src="https://www.youtube.com/embed/${videoId}" allowfullscreen></iframe>
            </div>
        </div>
    `;
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
}

function addSources(sources) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot';
    
    let sourcesHtml = `
        <div class="message-avatar">📚</div>
        <div class="message-content">
            <div class="sources">
                <strong>📌 Referenced Timestamps</strong>
    `;
    
    sources.slice(0, 3).forEach((source, i) => {
        sourcesHtml += `
            <div class="source-item">
                <strong>[${source.timestamp}]</strong>
                ${escapeHtml(source.text.substring(0, 150))}...
            </div>
        `;
    });
    
    sourcesHtml += `
            </div>
        </div>
    `;
    
    msgDiv.innerHTML = sourcesHtml;
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
}

function removeMessage(id) {
    const msg = document.getElementById(id);
    if (msg) msg.remove();
}

function scrollToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
