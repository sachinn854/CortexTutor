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

// ── Fetch helpers ─────────────────────────────────────────────
async function fetchWithTimeout(url, options = {}, timeoutMs = 120000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const res = await fetch(url, { ...options, signal: controller.signal });
        clearTimeout(id);
        return res;
    } catch (err) {
        clearTimeout(id);
        if (err.name === 'AbortError') throw new Error('Request timed out.');
        throw err;
    }
}

// Fetches a URL through a CORS proxy, trying corsproxy.io then allorigins.win.
async function proxyFetch(targetUrl, timeoutMs = 25000) {
    try {
        const r = await fetchWithTimeout(
            'https://corsproxy.io/?' + encodeURIComponent(targetUrl), {}, timeoutMs
        );
        if (r.ok) return await r.text();
    } catch(e) { /* fall through to second proxy */ }

    const r2 = await fetchWithTimeout(
        'https://api.allorigins.win/get?url=' + encodeURIComponent(targetUrl), {}, timeoutMs
    );
    if (!r2.ok) throw new Error(`All proxies failed (${r2.status})`);
    const j = await r2.json();
    if (!j.contents) throw new Error('Proxy returned empty content');
    return j.contents;
}

// ── Init ──────────────────────────────────────────────────────
function init() {
    addWelcomeCard();
    checkBackendHealth();

    sendBtn.addEventListener('click', handleSend);
    userInput.addEventListener('keypress', e => {
        if (e.key === 'Enter' && !state.isProcessing) handleSend();
    });
}

async function checkBackendHealth() {
    try {
        const res = await fetch('/health', { method: 'GET' });
        if (!res.ok) addBotMessage('**Warning:** Backend returned an error on startup. Try refreshing.');
    } catch {
        addBotMessage('**Backend starting…** The server is waking up. Please wait 30 seconds and refresh the page.');
    }
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

// ── Extract Video ID ──────────────────────────────────────────
function extractVideoId(url) {
    try {
        if (url.includes('youtu.be/')) return url.split('youtu.be/')[1].split(/[?#]/)[0];
        const u = new URL(url);
        return u.searchParams.get('v') || '';
    } catch { return ''; }
}

// ── Browser-side Transcript Fetch (via CORS proxy) ────────────
async function fetchTranscriptInBrowser(videoId) {
    const pageUrl = `https://www.youtube.com/watch?v=${videoId}`;

    // Fetch the YouTube page HTML — tries corsproxy.io then allorigins.win
    const html = await proxyFetch(pageUrl, 25000);

    // Extract ytInitialPlayerResponse JSON using brace-depth counting
    const marker = 'ytInitialPlayerResponse = ';
    const markerIdx = html.indexOf(marker);
    if (markerIdx === -1) throw new Error('Could not find player response in page');

    const jsonStart = markerIdx + marker.length;
    let depth = 0, i = jsonStart, inStr = false, escaped = false;
    for (; i < html.length; i++) {
        const c = html[i];
        if (escaped) { escaped = false; continue; }
        if (c === '\\' && inStr) { escaped = true; continue; }
        if (c === '"') { inStr = !inStr; continue; }
        if (inStr) continue;
        if (c === '{') depth++;
        else if (c === '}') { depth--; if (depth === 0) { i++; break; } }
    }
    const playerResp = JSON.parse(html.slice(jsonStart, i));

    // Get caption tracks
    const tracks = playerResp?.captions?.playerCaptionsTracklistRenderer?.captionTracks;
    if (!tracks?.length) throw new Error('No captions available for this video');

    // Prefer English, else first available
    const track = tracks.find(t => t.languageCode?.startsWith('en')) || tracks[0];
    const captionUrl = track.baseUrl + '&fmt=json3';

    // Fetch the actual captions
    const captText = await proxyFetch(captionUrl, 20000);
    const capData = JSON.parse(captText);

    // Parse json3 events into timestamped text
    const events = capData.events || [];
    const lines = [];
    for (const ev of events) {
        if (!ev.segs) continue;
        const text = ev.segs.map(s => s.utf8 || '').join('').replace(/\n/g, ' ').trim();
        if (!text) continue;
        const sec = (ev.tStartMs || 0) / 1000;
        const m = Math.floor(sec / 60);
        const s = Math.floor(sec % 60).toString().padStart(2, '0');
        lines.push(`[${m}:${s}] ${text}`);
    }

    if (!lines.length) throw new Error('Transcript is empty');
    return lines.join('\n');
}

// ── Process Video ─────────────────────────────────────────────
async function processVideo(url) {
    state.isProcessing = true;
    setInputState(false);
    userInput.value = '';

    const wc = document.getElementById('welcome-card');
    if (wc) wc.remove();

    addUserMessage(url);
    let loadingId = addBotMessage('Fetching transcript…', true);

    let serverBlocked = false;

    try {
        const res = await fetchWithTimeout(API + '/ingest/video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        }, 120000);
        const data = await res.json();
        removeMessage(loadingId);

        if (res.ok) {
            onVideoLoaded(data, url);
            state.isProcessing = false;
            setInputState(true);
            return;
        }

        const errType = data.detail?.error_type || '';
        serverBlocked = errType === 'NetworkResolutionError' || errType === 'RequestBlocked' ||
                        (data.detail?.message || '').toLowerCase().includes('unreachable');

        if (!serverBlocked) {
            const msg = data.detail?.message || 'Failed to load video.';
            addBotMessage(`**Error:** ${msg}\n\nMake sure the video has captions/subtitles enabled.`);
            state.isProcessing = false;
            setInputState(true);
            return;
        }
    } catch (err) {
        removeMessage(loadingId);
        addBotMessage(`**Network error:** ${err.message}`);
        state.isProcessing = false;
        setInputState(true);
        return;
    }

    // ── Server is blocked → try browser-side fetch ────────────
    const videoId = extractVideoId(url);
    loadingId = addBotMessage('Server blocked by YouTube. Trying browser method…', true);

    try {
        const transcript = await fetchTranscriptInBrowser(videoId);
        removeMessage(loadingId);
        loadingId = addBotMessage('Transcript fetched! Building knowledge base…', true);

        const res2 = await fetchWithTimeout(API + '/ingest/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                transcript_text: transcript,
                video_id: videoId || undefined,
                title: url
            })
        }, 60000);
        const data2 = await res2.json();
        removeMessage(loadingId);

        if (res2.ok) {
            onVideoLoaded(data2, url, videoId);
        } else {
            addBotMessage(`**Error:** ${data2.detail?.message || 'Failed to process transcript.'}`);
        }
    } catch (browserErr) {
        removeMessage(loadingId);
        // Both server and browser failed — show manual paste UI
        showTranscriptFallback(url);
    }

    state.isProcessing = false;
    setInputState(true);
}

function onVideoLoaded(data, url, playerVideoId) {
    const vid = playerVideoId || data.video_id;
    state.videoId = data.video_id;
    showVideoStatus(data.video_id);
    if (vid && vid.length === 11) addVideoPlayer(vid);
    addBotMessage(
        `**Video loaded successfully!**\n\n` +
        `📝 Chunks: **${data.total_chunks || data.total_segments}**\n\n` +
        `Ask me anything about this video — questions, summaries, timestamps. ` +
        `Or use the **Notes** / **MCQs** buttons above the input.`
    );
    userInput.placeholder = 'Ask anything about this video…';
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
        const res = await fetchWithTimeout(API + '/chat/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_id:   state.videoId,
                question,
                session_id: state.sessionId
            })
        }, 60000);
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
    const label     = command === 'notes' ? 'study notes' : command === 'mcqs' ? 'quiz questions' : 'flashcards';
    const loadingId = addBotMessage(`Generating ${label}…`, true);

    try {
        const res = await fetchWithTimeout(API + '/chat/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_id:   state.videoId,
                question:   originalQuestion,
                session_id: state.sessionId
            })
        }, 90000);
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
    const statusEl     = document.getElementById('video-status');
    const statusText   = document.getElementById('video-status-text');
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
    const id  = 'msg_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6);
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

// ── Manual Transcript Fallback (last resort) ──────────────────
function showTranscriptFallback(youtubeUrl) {
    const videoId = extractVideoId(youtubeUrl);

    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot';
    msgDiv.id = 'transcript-fallback';
    msgDiv.innerHTML = `
        <div class="message-avatar">⚠️</div>
        <div class="message-content">
            <div class="fallback-card">
                <p class="fallback-title">Auto-fetch failed — paste transcript manually</p>
                <p class="fallback-sub">Both server and browser methods failed. Copy the transcript from YouTube:</p>
                <ol class="fallback-steps">
                    <li>Open → <a href="${youtubeUrl}" target="_blank" rel="noopener" style="color:var(--cyan)">${youtubeUrl}</a></li>
                    <li>Click <strong>⋯ More</strong> below the video</li>
                    <li>Click <strong>Show transcript</strong></li>
                    <li>Select all (<kbd>Ctrl+A</kbd>) → Copy (<kbd>Ctrl+C</kbd>)</li>
                    <li>Paste below</li>
                </ol>
                <textarea id="manual-transcript" class="transcript-textarea" placeholder="Paste transcript here…"></textarea>
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
        textarea.style.borderColor = 'var(--red, #ef4444)';
        return;
    }

    const btn = document.querySelector('.submit-transcript-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Loading…'; }

    try {
        const res = await fetchWithTimeout(API + '/ingest/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                transcript_text: text,
                video_id: videoId || undefined,
                title: youtubeUrl
            })
        }, 60000);
        const data = await res.json();

        document.getElementById('transcript-fallback')?.remove();

        if (res.ok) {
            state.videoId = data.video_id;
            showVideoStatus(data.video_id);
            if (videoId) addVideoPlayer(videoId);
            addBotMessage(
                `**Transcript loaded!**\n\n📝 Chunks: **${data.total_chunks}**\n\nAsk me anything!`
            );
            userInput.placeholder = 'Ask anything about this video…';
        } else {
            addBotMessage(`**Error:** ${data.detail?.message || 'Failed to load transcript.'}`);
        }
    } catch (err) {
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
