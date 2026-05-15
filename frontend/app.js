// Relative URL — works on localhost AND on HF Spaces without any change
const API = "/api";

let state = {
    videoId: null,
    sessionId: 'session_' + Date.now(),
    isProcessing: false
};

const messagesDiv = document.getElementById('messages');
const userInput   = document.getElementById('user-input');
const sendBtn     = document.getElementById('send-btn');

// ── Init ──────────────────────────────────────────────────────
function init() {
    addWelcomeCard();

    sendBtn.addEventListener('click', handleSend);
    userInput.addEventListener('keypress', e => {
        if (e.key === 'Enter' && !state.isProcessing) handleSend();
    });
}

// ── Welcome Card ──────────────────────────────────────────────
function addWelcomeCard() {
    const card = document.createElement('div');
    card.className = 'welcome-card';
    card.id = 'welcome-card';
    card.innerHTML = `
        <div class="welcome-icon">✦</div>
        <h2>CortexTutor</h2>
        <p>Paste any YouTube URL below and I'll extract the transcript, build a knowledge base, and answer your questions — with timestamps.</p>
        <div class="welcome-features">
            <span class="feature-chip">🔍 Semantic Q&A</span>
            <span class="feature-chip">⏱️ Timestamp Search</span>
            <span class="feature-chip">📝 Auto Notes</span>
            <span class="feature-chip">❓ MCQ Quiz</span>
        </div>
    `;
    messagesDiv.appendChild(card);
}

// ── Send Handler ──────────────────────────────────────────────
async function handleSend() {
    const input = userInput.value.trim();
    if (!input || state.isProcessing) return;

    const isYouTubeUrl = input.includes('youtube.com') || input.includes('youtu.be');

    if (!state.videoId && isYouTubeUrl) {
        await processVideo(input);
    } else if (state.videoId) {
        await askQuestion(input);
    } else {
        addBotMessage('Please paste a valid YouTube URL first to load a video.');
    }
}

// ── Process Video ─────────────────────────────────────────────
async function processVideo(url) {
    state.isProcessing = true;
    setInputState(false);
    userInput.value = '';

    // Remove welcome card
    const wc = document.getElementById('welcome-card');
    if (wc) wc.remove();

    addUserMessage(url);
    const loadingId = addBotMessage('Processing video… this may take 30–60 seconds.', true);

    try {
        const res  = await fetch(API + '/ingest/video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        const data = await res.json();
        removeMessage(loadingId);

        if (res.ok) {
            state.videoId = data.video_id;
            showVideoStatus(data.video_id);
            addVideoPlayer(data.video_id);
            addBotMessage(
                `**Video loaded successfully!**\n\n` +
                `📊 Duration: **${data.duration}** &nbsp;·&nbsp; ` +
                `📝 Segments: **${data.total_segments}**\n\n` +
                `Ask me anything about this video — questions, summaries, timestamps. ` +
                `Or use the **Notes** / **MCQs** buttons above the input.`
            );
            userInput.placeholder = 'Ask anything about this video…';
        } else {
            const errType = data.detail?.error_type || '';
            const isBlocked = errType === 'NetworkResolutionError' || errType === 'RequestBlocked' ||
                              (data.detail?.message || '').toLowerCase().includes('unreachable');
            if (isBlocked) {
                showTranscriptFallback(url);
            } else {
                const msg = data.detail?.message || 'Failed to load video.';
                addBotMessage(`**Error:** ${msg}\n\nMake sure the video has captions/subtitles enabled.`);
            }
        }
    } catch (err) {
        removeMessage(loadingId);
        addBotMessage(`**Network error:** ${err.message}`);
    }

    state.isProcessing = false;
    setInputState(true);
}

// ── Ask Question ──────────────────────────────────────────────
async function askQuestion(question) {
    state.isProcessing = true;
    setInputState(false);
    userInput.value = '';

    addUserMessage(question);

    const studyCommand = detectStudyCommand(question);
    if (studyCommand) {
        await handleStudyCommand(studyCommand, question);
        return;
    }

    const loadingId = addBotMessage('', true, true);

    try {
        const res  = await fetch(API + '/chat/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_id:   state.videoId,
                question,
                session_id: state.sessionId
            })
        });
        const data = await res.json();
        removeMessage(loadingId);

        if (res.ok) {
            addBotMessage(data.answer);
            if (data.sources?.length > 0) addSources(data.sources);
        } else {
            addBotMessage(`**Error:** ${data.detail?.message || 'Failed to get answer.'}`);
        }
    } catch (err) {
        removeMessage(loadingId);
        addBotMessage(`**Network error:** ${err.message}`);
    }

    state.isProcessing = false;
    setInputState(true);
}

// ── Study Commands ────────────────────────────────────────────
function detectStudyCommand(question) {
    const q = question.toLowerCase().trim();
    if (q.startsWith('/')) {
        const cmd = q.slice(1);
        if (['notes', 'note'].includes(cmd))                        return 'notes';
        if (['mcqs', 'mcq', 'quiz', 'questions'].includes(cmd))     return 'mcqs';
        if (['flashcards', 'flashcard', 'cards'].includes(cmd))     return 'flashcards';
    }
    if (q.includes('make notes') || q.includes('generate notes') || q.includes('give me notes')) return 'notes';
    if (q.includes('make quiz')  || q.includes('generate questions') || q.includes('mcq'))       return 'mcqs';
    if (q.includes('flashcards') || q.includes('make flashcards'))                               return 'flashcards';
    return null;
}

async function handleStudyCommand(command, originalQuestion) {
    const label    = command === 'notes' ? 'study notes' : command === 'mcqs' ? 'quiz questions' : 'flashcards';
    const loadingId = addBotMessage(`Generating ${label}…`, true);

    try {
        const res  = await fetch(API + '/chat/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_id:   state.videoId,
                question:   originalQuestion,
                session_id: state.sessionId
            })
        });
        const data = await res.json();
        removeMessage(loadingId);

        if (res.ok) {
            addBotMessage(data.answer);
            if (data.sources?.length > 0) addSources(data.sources);
        } else {
            addBotMessage(`**Error:** ${data.detail?.message || `Failed to generate ${label}.`}`);
        }
    } catch (err) {
        removeMessage(loadingId);
        addBotMessage(`**Network error:** ${err.message}`);
    } finally {
        state.isProcessing = false;
        setInputState(true);
    }
}

async function triggerStudyCommand(command) {
    if (!state.videoId || state.isProcessing) return;
    const commandText = `/${command}`;
    addUserMessage(commandText);
    await handleStudyCommand(command, commandText);
}

// ── UI Helpers ────────────────────────────────────────────────
function setInputState(enabled) {
    userInput.disabled  = !enabled;
    sendBtn.disabled    = !enabled;
    document.querySelectorAll('.action-chip').forEach(b => b.disabled = !enabled);
    if (enabled) userInput.focus();
}

function showVideoStatus(videoId) {
    const statusEl   = document.getElementById('video-status');
    const statusText = document.getElementById('video-status-text');
    const quickActions = document.getElementById('quick-actions');

    statusEl.classList.add('active');
    statusText.textContent = videoId;
    if (quickActions) quickActions.classList.add('visible');
}

function addUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'message user';
    div.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-content">${escapeHtml(text)}</div>
    `;
    messagesDiv.appendChild(div);
    scrollToBottom();
}

function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
        return marked.parse(text, { breaks: true });
    }
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML.replace(/\n/g, '<br>');
}

function addBotMessage(text, isLoading = false, isTyping = false) {
    const id  = 'msg_' + Date.now() + '_' + Math.random().toString(36).slice(2,6);
    const div = document.createElement('div');
    div.id        = id;
    div.className = 'message bot';

    if (isTyping) {
        div.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>`;
    } else if (isLoading) {
        div.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content loading-message">${escapeHtml(text)}</div>`;
    } else {
        div.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content markdown-body">${renderMarkdown(text)}</div>`;
    }

    messagesDiv.appendChild(div);
    scrollToBottom();
    return id;
}

function addVideoPlayer(videoId) {
    const div = document.createElement('div');
    div.className = 'message bot';
    div.innerHTML = `
        <div class="message-avatar">🎥</div>
        <div class="message-content" style="flex:1">
            <div class="video-player">
                <iframe src="https://www.youtube.com/embed/${videoId}" allowfullscreen loading="lazy"></iframe>
            </div>
        </div>`;
    messagesDiv.appendChild(div);
    scrollToBottom();
}

function addSources(sources) {
    const div = document.createElement('div');
    div.className = 'message bot';

    let html = `
        <div class="message-avatar">📌</div>
        <div class="message-content">
            <div class="sources">
                <strong>Referenced Timestamps</strong>`;

    sources.slice(0, 3).forEach(s => {
        const snippet = escapeHtml((s.text || '').substring(0, 140));
        html += `
                <div class="source-item">
                    <strong>[${s.timestamp}]</strong>${snippet}…
                </div>`;
    });

    html += `</div></div>`;
    div.innerHTML = html;
    messagesDiv.appendChild(div);
    scrollToBottom();
}

function removeMessage(id) {
    document.getElementById(id)?.remove();
}

function scrollToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

// ── Manual Transcript Fallback ────────────────────────────────
function showTranscriptFallback(youtubeUrl) {
    // Extract video ID from URL for later use
    let videoId = '';
    try {
        if (youtubeUrl.includes('youtu.be/')) {
            videoId = youtubeUrl.split('youtu.be/')[1].split('?')[0];
        } else {
            const u = new URL(youtubeUrl);
            videoId = u.searchParams.get('v') || '';
        }
    } catch(e) {}

    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot';
    msgDiv.id = 'transcript-fallback';
    msgDiv.innerHTML = `
        <div class="message-avatar">⚠️</div>
        <div class="message-content">
            <div class="fallback-card">
                <p class="fallback-title">YouTube is blocked on this server</p>
                <p class="fallback-sub">Hosted servers pe YouTube block hota hai. Transcript manually copy karo:</p>
                <ol class="fallback-steps">
                    <li>YouTube pe video kholo → <strong>${youtubeUrl}</strong></li>
                    <li>Video ke neeche <strong>...</strong> (More) pe click karo</li>
                    <li><strong>Show transcript</strong> select karo</li>
                    <li>Saara text select karo (<kbd>Ctrl+A</kbd>) aur copy karo (<kbd>Ctrl+C</kbd>)</li>
                    <li>Neeche paste karo</li>
                </ol>
                <textarea id="manual-transcript" class="transcript-textarea" placeholder="Transcript yahan paste karo..."></textarea>
                <button class="submit-transcript-btn" onclick="submitManualTranscript('${videoId}', '${youtubeUrl}')">
                    Load Transcript
                </button>
            </div>
        </div>
    `;
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
}

async function submitManualTranscript(videoId, youtubeUrl) {
    const textarea = document.getElementById('manual-transcript');
    const text = textarea ? textarea.value.trim() : '';
    if (!text) {
        textarea.style.borderColor = 'var(--red)';
        return;
    }

    const btn = document.querySelector('.submit-transcript-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Loading…'; }

    try {
        const res = await fetch(API + '/ingest/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                transcript_text: text,
                video_id: videoId || undefined,
                title: youtubeUrl
            })
        });
        const data = await res.json();

        // Remove fallback card
        document.getElementById('transcript-fallback')?.remove();

        if (res.ok) {
            state.videoId = data.video_id;
            showVideoStatus(data.video_id);
            // Show player only if we have a real YouTube video ID
            if (videoId) addVideoPlayer(videoId);
            addBotMessage(
                `**Transcript loaded!**\n\n` +
                `📝 Chunks: **${data.total_chunks}**\n\n` +
                `Ab questions poochh sakte ho. Notes aur MCQs bhi kaam karenge.`
            );
            userInput.placeholder = 'Ask anything about this video…';
        } else {
            addBotMessage(`**Error:** ${data.detail?.message || 'Failed to load transcript.'}`);
        }
    } catch(err) {
        addBotMessage(`**Network error:** ${err.message}`);
    }

    state.isProcessing = false;
    setInputState(true);
}

// ── Boot ──────────────────────────────────────────────────────
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
