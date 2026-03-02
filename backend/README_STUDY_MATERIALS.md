# 📚 Study Materials Feature

## Overview

The Study Materials feature automatically generates learning materials from YouTube videos, including:

- **Summary**: Overview, key points, prerequisites, and learning outcomes
- **Flashcards**: Q&A pairs for self-testing (10-12 cards per video)
- **Key Takeaways**: 5 main points from the video

## How It Works

### Automatic Generation

When you ingest a video using `/api/ingest/video`, study materials are automatically generated in the background. This doesn't block the ingestion process.

```bash
# Ingest video (materials generated automatically)
POST http://localhost:8000/api/ingest/video
{
  "url": "https://www.youtube.com/watch?v=aircAruvnKk"
}
```

### Retrieve Materials

After ingestion completes (usually 30-60 seconds), retrieve the materials:

```bash
# Get study materials
GET http://localhost:8000/api/study-materials/{video_id}
```

### Manual Generation

If materials weren't generated or you want to regenerate them:

```bash
# Manually generate materials
POST http://localhost:8000/api/study-materials/generate/{video_id}
```

## API Endpoints

### GET `/api/study-materials/{video_id}`

Retrieve study materials for a video.

**Response:**
```json
{
  "status": "success",
  "materials": {
    "video_id": "aircAruvnKk",
    "summary": {
      "overview": "This video introduces neural networks...",
      "key_points": [
        "Neural network architecture",
        "Activation functions",
        "Backpropagation"
      ],
      "prerequisites": [
        "Basic calculus",
        "Linear algebra"
      ],
      "learning_outcomes": [
        "Understand neural network structure",
        "Learn how neurons process information"
      ]
    },
    "flashcards": [
      {
        "question": "What is a neural network?",
        "answer": "A computational model inspired by biological neural networks.",
        "timestamp": "02:30"
      }
    ],
    "key_takeaways": [
      "Neural networks mimic brain structure",
      "They learn from data through training"
    ]
  }
}
```

### POST `/api/study-materials/generate/{video_id}`

Manually trigger study material generation.

**Response:** Same as GET endpoint

## Storage

Study materials are stored in:
```
study_materials/
  {video_id}/
    materials.json
```

## Use Cases

1. **Quick Review**: Get a summary before watching the full video
2. **Self-Assessment**: Use flashcards to test your understanding
3. **Study Planning**: Check prerequisites to know what to learn first
4. **Exam Prep**: Review key takeaways for quick revision

## Integration Ideas

- Export flashcards to Anki format
- Create study schedules based on prerequisites
- Track which flashcards you've mastered
- Generate quizzes from flashcards

## Limitations

- Materials quality depends on LLM performance
- Works best with educational/tutorial videos
- May take 30-60 seconds to generate
- Limited to first 3000 characters of transcript (to avoid token limits)

## Future Enhancements

- [ ] Anki export format
- [ ] Difficulty levels for flashcards
- [ ] Spaced repetition scheduling
- [ ] Multi-language support
- [ ] Custom material templates
