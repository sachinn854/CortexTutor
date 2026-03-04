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
                `💬 **Ask me anything about this video!**\n\n` +
                `🎯 **Quick Commands:**\n` +
                `• \`/notes\` - Get structured study notes\n` +
                `• \`/mcqs\` - Generate quiz questions\n` +
                `• \`/flashcards\` - Create flashcards\n\n` +
                `Or just ask questions naturally!`
            );
            
            // Add study materials buttons
            console.log('🎯 Adding study materials buttons for video:', state.videoId);
            addStudyMaterialsButtons(state.videoId);
            console.log('✅ Study materials buttons added');
            
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
    
    // Check if it's a study command
    const studyCommand = detectStudyCommand(question);
    if (studyCommand) {
        await handleStudyCommand(studyCommand, question);
        return;
    }
    
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

// Study Command Detection and Handling
function detectStudyCommand(question) {
    const q = question.toLowerCase().trim();
    
    if (q.startsWith('/')) {
        const cmd = q.substring(1);
        if (['notes', 'note'].includes(cmd)) return 'notes';
        if (['mcqs', 'mcq', 'quiz', 'questions'].includes(cmd)) return 'mcqs';
        if (['flashcards', 'flashcard', 'cards'].includes(cmd)) return 'flashcards';
    }
    
    // Natural language detection
    if (q.includes('make notes') || q.includes('generate notes') || q.includes('give me notes')) return 'notes';
    if (q.includes('make quiz') || q.includes('generate questions') || q.includes('mcq')) return 'mcqs';
    if (q.includes('make flashcards') || q.includes('generate cards') || q.includes('flashcards')) return 'flashcards';
    
    return null;
}

async function handleStudyCommand(command, originalQuestion) {
    const loadingId = addBotMessage(`📚 Generating ${command}...`, true);
    
    try {
        const res = await fetch(API + '/chat/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                video_id: state.videoId, 
                question: originalQuestion,
                session_id: state.sessionId 
            })
        });

        const data = await res.json();
        removeMessage(loadingId);

        if (res.ok) {
            // Display the study material response
            addBotMessage(data.answer);
            if (data.sources && data.sources.length > 0) {
                addSources(data.sources);
            }
        } else {
            const errorMsg = data.detail?.message || `Failed to generate ${command}`;
            addBotMessage(`❌ Error: ${errorMsg}`);
        }
    } catch (err) {
        console.error('❌ Error:', err);
        removeMessage(loadingId);
        addBotMessage(`❌ Network error: ${err.message}`);
    } finally {
        state.isProcessing = false;
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
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


// Study Materials Buttons
function addStudyMaterialsButtons(videoId) {
    console.log('📚 Creating study materials buttons for videoId:', videoId);
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot';
    msgDiv.innerHTML = `
        <div class="message-avatar">📚</div>
        <div class="message-content">
            <div class="study-materials-buttons">
                <p style="margin-bottom: 12px; font-weight: 600;">📖 Generate Study Materials:</p>
                <button class="study-btn" onclick="triggerStudyCommand('notes')">📝 Notes</button>
                <button class="study-btn" onclick="triggerStudyCommand('mcqs')">❓ MCQs</button>
            </div>
        </div>
    `;
    messagesDiv.appendChild(msgDiv);
    console.log('✅ Study materials buttons appended to DOM');
    scrollToBottom();
}

async function triggerStudyCommand(command) {
    if (!state.videoId || state.isProcessing) return;
    const commandText = `/${command}`;
    addUserMessage(commandText);
    await handleStudyCommand(command, commandText);
}
