# 🎨 Frontend - YouTube Learning Assistant

Simple, clean frontend built with HTML, CSS, JavaScript, and Tailwind CSS.

---

## 🚀 Quick Start

### 1. Start the Backend
```bash
cd backend
python -m app.main
```
Backend runs at: `http://localhost:8000`

### 2. Open the Frontend
Simply open `index.html` in your browser:
```bash
cd frontend
# On Windows
start index.html

# On Mac
open index.html

# On Linux
xdg-open index.html
```

Or use a simple HTTP server:
```bash
# Python 3
python -m http.server 8080

# Node.js (if you have it)
npx serve

# Then open: http://localhost:8080
```

---

## 📁 File Structure

```
frontend/
├── index.html      # Main HTML file
├── styles.css      # Custom CSS styles
├── app.js          # JavaScript logic
└── README.md       # This file
```

---

## ✨ Features

### 1. Video Ingestion
- Enter YouTube URL
- Submit for processing
- See ingestion status
- View video details

### 2. Chat Interface
- Ask questions about videos
- Get AI-powered answers
- See timestamp sources
- Click timestamps to jump to video
- Optional conversation memory

### 3. Study Materials
- View auto-generated summaries
- Interactive flashcards (click to flip)
- Key takeaways list
- Prerequisites and learning outcomes

### 4. Video Player
- Embedded YouTube player
- Syncs with chat timestamps
- Click source links to jump to specific moments

---

## 🎨 Design Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern UI**: Clean, professional interface with Tailwind CSS
- **Smooth Animations**: Slide-in messages, flip cards, loading indicators
- **Toast Notifications**: Success/error messages
- **Tab Navigation**: Easy switching between features
- **Dark Mode Ready**: Can be easily extended

---

## 🔧 Configuration

### Change API URL
Edit `app.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000/api';
// Change to your backend URL
```

### Customize Colors
Edit Tailwind classes in `index.html` or add custom CSS in `styles.css`.

---

## 📱 Usage Guide

### Ingest a Video
1. Click "Ingest Video" tab
2. Paste YouTube URL
3. Click "Ingest Video" button
4. Wait for processing (30-60 seconds)
5. Click "Start Chatting" when done

### Ask Questions
1. Click "Chat" tab
2. Enter video ID (from ingestion)
3. Type your question
4. Press Enter or click send
5. View answer with timestamp sources
6. Click timestamps to jump to video

### View Study Materials
1. Click "Study Materials" tab
2. Enter video ID
3. Click "Load" button
4. View summary, flashcards, and takeaways
5. Click flashcards to flip them

---

## 🎯 Features Breakdown

### Chat Features
- ✅ Real-time messaging
- ✅ Typing indicator
- ✅ Source citations with timestamps
- ✅ Conversation memory toggle
- ✅ Embedded video player
- ✅ Clickable timestamp links

### Study Materials Features
- ✅ Video summary with overview
- ✅ Key points list
- ✅ Prerequisites
- ✅ Learning outcomes
- ✅ Interactive flashcards
- ✅ Key takeaways

### UI/UX Features
- ✅ Toast notifications
- ✅ Loading indicators
- ✅ Error handling
- ✅ Smooth animations
- ✅ Responsive design
- ✅ Clean, modern interface

---

## 🐛 Troubleshooting

### CORS Errors
If you see CORS errors in the browser console:

1. Make sure backend is running
2. Check backend CORS settings in `backend/app/main.py`
3. Ensure `allow_origins` includes your frontend URL

### API Connection Failed
1. Verify backend is running at `http://localhost:8000`
2. Check API_BASE_URL in `app.js`
3. Test backend directly: `http://localhost:8000/docs`

### Video Not Loading
1. Ensure video was ingested successfully
2. Check video ID is correct
3. Verify video has transcripts enabled

### Study Materials Not Found
1. Wait 30-60 seconds after ingestion
2. Materials are generated in background
3. Try manual generation: `POST /api/study-materials/generate/{video_id}`

---

## 🎨 Customization

### Change Theme Colors
Edit Tailwind classes:
```html
<!-- Primary color (blue) -->
<button class="bg-blue-600 hover:bg-blue-700">

<!-- Change to green -->
<button class="bg-green-600 hover:bg-green-700">
```

### Add Dark Mode
Add to `styles.css`:
```css
@media (prefers-color-scheme: dark) {
    body {
        background-color: #1F2937;
        color: #F9FAFB;
    }
}
```

### Modify Layout
Edit `index.html` grid classes:
```html
<!-- Current: 2/3 chat, 1/3 video -->
<div class="lg:col-span-2">...</div>
<div class="lg:col-span-1">...</div>

<!-- Change to 1/2 each -->
<div class="lg:col-span-1">...</div>
<div class="lg:col-span-1">...</div>
```

---

## 📊 Browser Support

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Opera
- ⚠️ IE11 (not supported)

---

## 🚀 Deployment

### Deploy to Netlify/Vercel
1. Push to GitHub
2. Connect to Netlify/Vercel
3. Deploy (no build step needed!)
4. Update API_BASE_URL to production backend

### Deploy with Backend
1. Serve frontend from FastAPI:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

---

## 📝 Future Enhancements

Possible improvements:
- [ ] User authentication
- [ ] Save chat history
- [ ] Export study materials (PDF, Anki)
- [ ] Multiple video comparison
- [ ] Progress tracking
- [ ] Quiz mode UI
- [ ] Voice input
- [ ] Mobile app (React Native)

---

## 🎉 That's It!

You now have a fully functional frontend for your YouTube Learning Assistant!

**Enjoy learning! 🎓**
