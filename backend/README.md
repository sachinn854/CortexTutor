---
title: CortexTutor Backend
emoji: "🎓"
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# CortexTutor Backend

FastAPI backend for CortexTutor running in a Hugging Face Docker Space.

## Health Check

- Endpoint: `/health`
- Main API prefix: `/api`

## Notes

- `vector_db/` and `study_materials/` directories are auto-created at runtime.
- Set required secrets in Space settings (for example `GROQ_API_KEY`).
