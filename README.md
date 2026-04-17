# FastAPI Chat Backend (Simple)

Simple FastAPI backend with:
- Versioned REST API (`/api/v1`)
- PostgreSQL + SQLAlchemy (no Alembic)
- OpenAI/Anthropic/Llama provider abstraction
- Conversation history + summaries stored in PostgreSQL
- Structured JSON logs + `/metrics`
- Docker support

## Quickstart (uv)

```bash
uv sync --dev
cp .env.example .env
uv run uvicorn app.main:app --reload
```

On startup, the app auto-creates tables in PostgreSQL.

## Local PostgreSQL setup (`chatbot`)

Run these scripts in order:

```bash
psql -U postgres -d postgres -f scripts/db/01_create_database.sql
psql -U postgres -d chatbot -f scripts/db/02_schema.sql
```

Optional reset:

```bash
psql -U postgres -d chatbot -f scripts/db/03_reset.sql
```

## Run tests

```bash
uv run pytest
```

## API

Base path: `/api/v1`

- `POST /auth/signup`
- `POST /auth/login`
- `POST /chat`
- `POST /conversations` (start new conversation + first message)
- `GET /conversations?user_id=...` (list all conversations for user)
- `GET /conversations/{conversation_id}?user_id=...` (conversation detail with full history)
- `POST /conversations/{conversation_id}/messages` (add message to existing conversation)
- `DELETE /conversations/{conversation_id}?user_id=...` (delete conversation + messages)
- `GET /history/{user_id}` (optional `session_id` query)

## Docker

```bash
docker compose up --build
```

The compose stack starts:
- `api` (FastAPI)
- `postgres`

## Notes

- OpenAI provider is fully implemented.
- If `OPENAI_API_KEY` is not set, OpenAI uses a deterministic local stub response for development/testing.
