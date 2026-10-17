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


## Troubleshooting "Failed to fetch"

1. Start FastAPI from the repository root:
   `source .venv/bin/activate`
   `uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000`
2. Check `http://localhost:8000/health` returns `{"status":"healthy"}`.
3. Check `http://localhost:8000/api/chatbot/status`. It must report `"status":"configured"` and `"api_key_configured":true`.
4. If not configured, set `GROQ_API_KEY` in the repository-root `.env` file and restart FastAPI. Never put this secret in the frontend `.env.local`.
5. In a second terminal, run the frontend from `frontend` with `npm run dev`, then reload `http://localhost:3000`.
6. If status is configured but chat fails, inspect the FastAPI terminal and browser Network tab for `POST /backend-api/chatbot/chat`.

The status endpoint reports only whether a key exists; it never returns the key itself. A configured key does not guarantee provider quota or model availability.
