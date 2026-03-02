// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// Current video state
let currentVideoId = null;
let currentVideoUrl = null;
let sessionId = generateSessionId();

// Generate unique session ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Toast Notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const icon = document.getElementById('toast-icon');
    const messageEl = document.getElementById('toast-message');
    
    const icons = {
        success: '<i class="fas fa-check-circle text-green-500 text-2xl"></i>',
        error: '<i class="fas fa-exclamation-circle text-red-500 text-2xl"></i>',
        info: '<i class="fas fa-info-circle text-blue-500 text-2xl"></i>'
    };
    
    icon.innerHTML = icons[type] || icons.info;
    messageEl.textContent = message;
    
    toast.classList.remove('hidden');
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
        toast.classList.add('hide');
        setTimeout(() => {
            toast.classList.add('hidden');
            toast.classList.remove('hide');
        }, 300);
    }, 3000);
}

// Start Learning - Main entry point
async function startLearning() {
    const urlInput = document.getElementById('video-url-input');
    const url = urlInput.value.trim();
    
    if (!url) {
        showToast('Please enter a YouTube URL', 'error');
        return;
    }
    
    // Show loading
    document.getElementById('loading-section').classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_BASE_URL}/ingest/video`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Hide loading
            document.getElementById('loading-section').classList.add('hidden');
            
            // Store video info
            currentVideoId = data.video_id;
            currentVideoUrl = data.video_url;
            
            // Hide input section, show learning interface
            document.getElementById('video-input-section').classList.add('hidden');
            document.getElementById('learning-interface').classList.remove('hidden');
            
            // Load video player
            loadVideoPlayer(currentVideoId);
            
            // Show video info
            document.getElementById('video-info').innerHTML = `
                <p class="font-semibold">Duration: ${data.duration}</p>
                <p class="text-xs mt-1">Segments: ${data.total_segments} | Chunks: ${data.total_chunks}</p>
            `;
            
            showToast('Video loaded! Start asking questions', 'success');
            
            // Focus on question input
            setTimeout(() => {
                document.getElementById('question-input').focus();
            }, 100);
        } else {
            document.getElementById('loading-section').classList.add('hidden');
            showToast(data.detail?.message || 'Failed to load video', 'error');
        }
    } catch (error) {
        document.getElementById('loading-section').classList.add('hidden');
        showToast('Network error: ' + error.message, 'error');
    }
}

// Change Video
function changeVideo() {
    if (confirm('Are you sure you want to load a different video? Current chat will be cleared.')) {
        // Reset state
        currentVideoId = null;
        currentVideoUrl = null;
        sessionId = generateSessionId();
        
        // Clear chat
        document.getElementById('chat-messages').innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <i class="fas fa-comment-dots text-4xl mb-3"></i>
                <p>Ask me anything about this video!</p>
            </div>
        `;
        
        // Show input section, hide learning interface
        document.getElementById('video-input-section').classList.remove('hidden');
        document.getElementById('learning-interface').classList.add('hidden');
        document.getElementById('loading-section').classList.add('hidden');
        
        // Clear input
        document.getElementById('video-url-input').value = '';
    }
}

// Load Video Player
function loadVideoPlayer(videoId) {
    const playerDiv = document.getElementById('video-player');
    playerDiv.innerHTML = `
        <iframe 
            width="100%" 
            height="100%" 
            src="https://www.youtube.com/embed/${videoId}" 
            frameborder="0" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen
            class="rounded-lg"
        ></iframe>
    `;
}

// Ask Question
async function askQuestion() {
    const question = document.getElementById('question-input').value.trim();
    
    if (!question) {
        showToast('Please enter a question', 'error');
        return;
    }
    
    if (!currentVideoId) {
        showToast('Please load a video first', 'error');
        return;
    }
    
    // Add user message
    addMessage(question, 'user');
    
    // Clear input
    document.getElementById('question-input').value = '';
    
    // Show typing indicator
    const typingId = addTypingIndicator();
    
    try {
        const useSession = document.getElementById('use-session').checked;
        const requestBody = {
            video_id: currentVideoId,
            question: question
        };
        
        if (useSession) {
            requestBody.session_id = sessionId;
        }
        
        const response = await fetch(`${API_BASE_URL}/chat/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        removeTypingIndicator(typingId);
        
        if (response.ok) {
            addMessage(data.answer, 'assistant', data.sources);
        } else {
            addMessage(`Error: ${data.detail?.message || 'Failed to get answer'}`, 'assistant');
            showToast('Failed to get answer', 'error');
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage(`Network error: ${error.message}`, 'assistant');
        showToast('Network error', 'error');
    }
}

// Ask Quick Question
function askQuickQuestion(question) {
    document.getElementById('question-input').value = question;
    askQuestion();
}

// Add Message to Chat
function addMessage(text, sender, sources = []) {
    const messagesDiv = document.getElementById('chat-messages');
    
    // Remove welcome message if exists
    const welcome = messagesDiv.querySelector('.text-center');
    if (welcome) {
        welcome.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = '<div class="mt-2 text-sm">';
        sourcesHtml += '<p class="font-semibold mb-1">Jump to:</p>';
        sources.forEach((source, index) => {
            sourcesHtml += `
                <a href="${source.url}" target="_blank" class="source-link">
                    <i class="fas fa-clock mr-1"></i>${source.timestamp}
                </a>
            `;
        });
        sourcesHtml += '</div>';
    }
    
    messageDiv.innerHTML = `
        <div class="message-bubble">
            <p>${text}</p>
            ${sourcesHtml}
        </div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Add Typing Indicator
function addTypingIndicator() {
    const messagesDiv = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    const id = 'typing-' + Date.now();
    typingDiv.id = id;
    typingDiv.className = 'message assistant';
    typingDiv.innerHTML = `
        <div class="message-bubble">
            <div class="flex space-x-2">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
            </div>
        </div>
    `;
    messagesDiv.appendChild(typingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return id;
}

// Remove Typing Indicator
function removeTypingIndicator(id) {
    const typingDiv = document.getElementById(id);
    if (typingDiv) {
        typingDiv.remove();
    }
}

// Toggle Study Materials
async function toggleStudyMaterials() {
    const modal = document.getElementById('study-materials-modal');
    
    if (modal.classList.contains('hidden')) {
        // Show modal
        modal.classList.remove('hidden');
        
        // Load materials
        if (currentVideoId) {
            await loadStudyMaterialsForCurrentVideo();
        }
    } else {
        // Hide modal
        modal.classList.add('hidden');
    }
}

// Load Study Materials for Current Video
async function loadStudyMaterialsForCurrentVideo() {
    const contentDiv = document.getElementById('study-materials-content');
    
    // Show loading
    contentDiv.innerHTML = `
        <div class="text-center py-8">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
            <p class="mt-3 text-gray-600">Loading study materials...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_BASE_URL}/study-materials/${currentVideoId}`);
        const data = await response.json();
        
        if (response.ok) {
            displayStudyMaterials(data.materials);
        } else {
            contentDiv.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-exclamation-circle text-4xl mb-3"></i>
                    <p>${data.detail?.message || 'Study materials not ready yet'}</p>
                    <p class="text-sm mt-2">They are being generated in the background. Please try again in a minute.</p>
                </div>
            `;
        }
    } catch (error) {
        contentDiv.innerHTML = `
            <div class="text-center py-8 text-red-500">
                <i class="fas fa-exclamation-circle text-4xl mb-3"></i>
                <p>Failed to load study materials</p>
            </div>
        `;
    }
}

// Display Study Materials
function displayStudyMaterials(materials) {
    const contentDiv = document.getElementById('study-materials-content');
    
    contentDiv.innerHTML = `
        <div class="space-y-6">
            <!-- Summary -->
            <div class="border border-gray-200 rounded-lg p-6">
                <h3 class="text-xl font-bold text-gray-800 mb-4">
                    <i class="fas fa-file-alt text-green-600 mr-2"></i>Summary
                </h3>
                <div class="space-y-4">
                    <div>
                        <h4 class="font-semibold text-gray-700 mb-2">Overview</h4>
                        <p class="text-gray-600">${materials.summary.overview}</p>
                    </div>
                    <div>
                        <h4 class="font-semibold text-gray-700 mb-2">Key Points</h4>
                        <ul class="list-disc list-inside space-y-1 text-gray-600">
                            ${materials.summary.key_points.map(point => `<li>${point}</li>`).join('')}
                        </ul>
                    </div>
                    <div>
                        <h4 class="font-semibold text-gray-700 mb-2">Prerequisites</h4>
                        <ul class="list-disc list-inside space-y-1 text-gray-600">
                            ${materials.summary.prerequisites.map(prereq => `<li>${prereq}</li>`).join('')}
                        </ul>
                    </div>
                    <div>
                        <h4 class="font-semibold text-gray-700 mb-2">Learning Outcomes</h4>
                        <ul class="list-disc list-inside space-y-1 text-gray-600">
                            ${materials.summary.learning_outcomes.map(outcome => `<li>${outcome}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Flashcards -->
            <div class="border border-gray-200 rounded-lg p-6">
                <h3 class="text-xl font-bold text-gray-800 mb-4">
                    <i class="fas fa-layer-group text-purple-600 mr-2"></i>Flashcards
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${materials.flashcards && materials.flashcards.length > 0 ? 
                        materials.flashcards.map((card, index) => `
                            <div class="flashcard" onclick="flipCard(${index})">
                                <div class="flashcard-inner" id="flashcard-${index}">
                                    <div class="flashcard-front">
                                        <div>
                                            <p class="text-lg font-semibold mb-2">Question</p>
                                            <p>${card.question}</p>
                                        </div>
                                    </div>
                                    <div class="flashcard-back">
                                        <div>
                                            <p class="text-lg font-semibold mb-2">Answer</p>
                                            <p>${card.answer}</p>
                                            ${card.timestamp ? `<p class="mt-2 text-sm"><i class="fas fa-clock mr-1"></i>${card.timestamp}</p>` : ''}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('') 
                        : '<p class="text-gray-500">No flashcards available</p>'
                    }
                </div>
            </div>

            <!-- Key Takeaways -->
            <div class="border border-gray-200 rounded-lg p-6">
                <h3 class="text-xl font-bold text-gray-800 mb-4">
                    <i class="fas fa-lightbulb text-yellow-600 mr-2"></i>Key Takeaways
                </h3>
                ${materials.key_takeaways && materials.key_takeaways.length > 0 ?
                    `<ul class="space-y-3">
                        ${materials.key_takeaways.map((takeaway, index) => `
                            <li class="flex items-start">
                                <span class="flex-shrink-0 w-8 h-8 bg-yellow-100 text-yellow-600 rounded-full flex items-center justify-center font-bold mr-3">
                                    ${index + 1}
                                </span>
                                <p class="text-gray-700 pt-1">${takeaway}</p>
                            </li>
                        `).join('')}
                    </ul>`
                    : '<p class="text-gray-500">No key takeaways available</p>'
                }
            </div>
        </div>
    `;
}

// Flip Flashcard
function flipCard(index) {
    const card = document.getElementById(`flashcard-${index}`).parentElement;
    card.classList.toggle('flipped');
}
