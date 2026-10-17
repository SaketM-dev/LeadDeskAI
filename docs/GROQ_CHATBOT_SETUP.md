# LeadDeskAI Groq chatbot setup

The global chat widget calls the FastAPI endpoint through the Next.js backend rewrite:
`POST /backend-api/chatbot/chat` -> FastAPI `POST /api/chatbot/chat`.

## Backend environment

Set these variables in the environment where FastAPI runs (for local development, in the backend's ignored `.env` file; in deployment, use the hosting provider's secret/environment-variable settings):

```env
GROQ_API_KEY=your_rotated_groq_key
GROQ_MODEL=openai/gpt-oss-20b
```

Never use a `NEXT_PUBLIC_` prefix for the key and never commit the actual key. Rotate any key that has been shared publicly.

## Local run

Run the FastAPI backend from the `backend` directory using the project's existing environment, then run the frontend from `frontend`. The frontend rewrite uses `BACKEND_API_URL` (default `http://localhost:8000`) to reach FastAPI.

## Behavior and limitations

- The widget is rendered in the shared app layout, including the public landing page.
- The backend loads `knowledge_base/KNOWLEDGE_BASE.md` and `knowledge_base/courses.json` as prompt context.
- Missing course facts must not be guessed; update the approved knowledge base to change official answers.
- This first version is text-only. It does not book calendar slots or send reminders.
- Groq usage is subject to the selected model's current availability, rate limits, and pricing.
