# gemini-live-api-hackathon
Live API hackathon

- To run locally, use: `uv run uvicorn app.main:app --reload`

## Gmail push flow

This repo now includes a Gmail Push Notification webhook at `POST /gmail/webhook` that:

- decodes the Pub/Sub push payload
- persists the latest processed `historyId` in PostgreSQL
- persists each processed meeting invite email in `meeting_invite` with extracted meeting status
- calls `users.history.list(startHistoryId=...)` with pagination
- fetches each new message via `users.messages.get`
- stores failed Recall bot create/update/stop actions in a manual-review queue
- marks the account as `resync_required` if Gmail returns `404 historyId too old`

## Database setup

The Gmail history state now uses `SQLModel` with `Alembic` migrations over an async `asyncpg` connection.

Preferred environment variable:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/postgres
```

If the app runs on your host machine and Postgres comes from `docker compose`, use `127.0.0.1`.

If the app itself later runs inside Docker Compose on the same network as the database service, then `db` is correct:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/postgres
```

Component-based fallback variables are still supported, but only the port/user/password/db pieces are needed for local development:

```bash
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
```

If you are using the included Docker Compose Postgres service, start it with:

```bash
docker compose up -d db
```

Install and lock the new dependencies, then run the migration:

```bash
uv sync
uv run alembic upgrade head
```

Create a new migration later with:

```bash
uv run alembic revision --autogenerate -m "describe change"
```

If you pull the new Recall fallback queue changes, run:

```bash
uv run alembic upgrade head
```

That migration set now also includes the `meeting_invite` table used to store meeting invite emails and statuses.

Manual review endpoints for failed Recall bot automation:

```bash
GET /api/recall/failures
POST /api/recall/failures/{queue_id}/resolve
PATCH /api/recall/bots/{bot_id}
```

Required environment variables:

```bash
GMAIL_WATCH_TOPIC=projects/<project-id>/topics/<topic-name>
GMAIL_ALLOWED_EMAIL_ADDRESSES_CSV=user@gmail.com
```

Optional environment variables:

```bash
GMAIL_WATCH_LABEL_IDS_CSV=INBOX
```

To bootstrap the watch baseline, run:

```bash
uv run python -m app.gmail_watch
```

That command starts `users.watch`, prints the Gmail response, and stores the returned `historyId` so later Pub/Sub notifications can query incremental updates correctly.

## Demo

Start the FastAPI app:

```bash
uv run uvicorn app.main:app --reload
```

or

```bash
fastapi dev
```

Then open `http://127.0.0.1:8000` in your browser to use the original Gemini Live demo UI.

The new read-only meeting dashboard is mounted at `http://127.0.0.1:8000/dashboard/`.
It uses the existing `meeting_invite` table as its data source, so the upcoming calendar panel reflects persisted Gmail invite emails rather than a live Google Calendar sync.

<!--
## Minimal Recall Bot Setup (No Recording)

This repo now includes a minimal Recall output media runtime page at `/recall`.

### 1) Run the app

```bash
uv run uvicorn app.main:app --reload
```

### 2) Expose the frontend publicly

Use ngrok (or equivalent) so Recall can load your page:

```bash
ngrok http 8000
```

Use the generated HTTPS URL for the bot payload.

### 3) Create bot (without recording config)

```json
{
	"meeting_url": "YOUR_MEETING_URL",
	"bot_name": "My Gemini Agent",
	"output_media": {
		"camera": {
			"kind": "webpage",
			"config": {
				"url": "https://your-ngrok-url.ngrok-free.app/recall?wss=wss%3A%2F%2Fyour-ngrok-url.ngrok-free.app%2Fws%2Frecall-bot%2F%7Bsession_id%7D"
			}
		}
	},
	"variant": {
		"zoom": "web_4_core",
		"google_meet": "web_4_core",
		"microsoft_teams": "web_4_core"
	}
}
```

### 4) Runtime behavior in `/recall`

- Auto-connects meeting audio and Gemini Live websocket on page load.
- Connects to the existing Gemini Live websocket at `/ws/recall-bot/{session_id}` by default.
- Also supports Recall-demo style `wss=` query param override, including `{session_id}` placeholder substitution.
- Captures meeting audio with `getUserMedia({ audio: true })`, resamples to 16k PCM, and streams it directly to Gemini Live over the websocket.
- Renders a visible conversation panel from Gemini Live text and transcription events.
- Plays Gemini Live PCM audio when the browser runtime allows Web Audio output.

You can prefill transcript websocket URL with:

`/recall?transcript_ws=wss%3A%2F%2Fmeeting-data.bot.recall.ai%2Fapi%2Fv1%2Ftranscript`

The Recall integration now uses only two relevant app surfaces:

- `GET /recall`
- `WS /ws/{user_id}/{session_id}`
-->