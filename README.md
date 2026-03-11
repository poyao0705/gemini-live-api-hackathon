# Meeting Host AI

A **silent-by-default AI meeting co-host** built on the Gemini Live API. It joins meetings via [Recall AI](https://www.recall.ai/), listens in real time, captures decisions and action items, and only speaks when addressed ("Hey Gemini") or when the conversation drifts off-agenda.

The app auto-discovers meeting invites from Gmail and schedules Recall bots to join them automatically.

---

## Architecture overview

```
Gmail ──► Google Cloud Pub/Sub ──► POST /gmail/webhook
                                        │
                                        ├─► parse meeting invite
                                        └─► schedule Recall AI bot
                                                │
                                                └─► bot streams audio
                                                        │
                                                        └─► WebSocket /ws/{user}/{session}
                                                                │
                                                                └─► Gemini Live API (ADK)
```

- **FastAPI** serves the REST API and a **FastHTML** web dashboard.
- **Google ADK** (`Runner.run_live`) powers the real-time bidirectional audio stream with Gemini.
- **Recall AI** joins the video call as a bot and forwards audio to the WebSocket endpoint.
- **PostgreSQL** (via Docker Compose) stores Gmail history state, meeting invites, and failed-bot queues.
- **Alembic** manages database migrations.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | ≥ 3.13 | `python3 --version` |
| [uv](https://docs.astral.sh/uv/) | latest | package manager / venv |
| Docker / Docker Compose | any recent | for the Postgres container |
| Google Cloud project | — | OAuth2 credentials + Pub/Sub topic |
| [Recall AI](https://www.recall.ai/) account | — | API token |

---

## 1. Clone and install dependencies

```bash
git clone <repo-url>
cd gemini-live-api-hackathon
uv sync
```

All dependencies (including dev) are declared in `pyproject.toml`. `uv sync` creates `.venv` automatically.

---

## 2. Google OAuth2 credentials

This app authenticates to Gmail using a desktop OAuth2 flow.

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services → Credentials**.
2. Create an **OAuth 2.0 Client ID** of type **Desktop app**.
3. Download the JSON and save it as `credentials.json` in the repo root.
4. Enable the **Gmail API** and **Google People API** on your project.

On first run (or when running the watch bootstrap below) a browser window will open asking you to authorise the app. The resulting token is cached to `token.json` in the repo root.

> `credentials.json` and `token.json` are already in `.gitignore`. Do not commit them.

---

## 3. Google Cloud Pub/Sub (Gmail push notifications)

Gmail push notifications require a verified Pub/Sub topic.

1. Create a topic in your GCP project:
   ```bash
   gcloud pubsub topics create gmail-push
   ```
2. Grant the Gmail service account publish rights:
   ```bash
   gcloud pubsub topics add-iam-policy-binding gmail-push \
     --member="serviceAccount:gmail-api-push@system.gserviceaccount.com" \
     --role="roles/pubsub.publisher"
   ```
3. Create a **push subscription** pointing to your app's public webhook URL:
   ```bash
   gcloud pubsub subscriptions create gmail-push-sub \
     --topic=gmail-push \
     --push-endpoint=https://<your-public-host>/gmail/webhook \
     --ack-deadline=60
   ```
   For local development, use a tunnel such as [ngrok](https://ngrok.com/):
   ```bash
   ngrok http 8000
   # then use the https://... URL as --push-endpoint
   ```

---

## 4. Environment variables

Create a `.env` file in the repo root (the app loads both `app/.env` and `.env`):

```bash
# ── Database ────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/postgres

# ── Gmail ───────────────────────────────────────────────────────
# Full Pub/Sub topic resource name
GMAIL_WATCH_TOPIC=projects/<gcp-project-id>/topics/gmail-push

# Comma-separated list of Gmail addresses whose incoming mail is processed
GMAIL_ALLOWED_EMAIL_ADDRESSES_CSV=you@gmail.com

# Optional: restrict to specific label IDs (default: INBOX)
# GMAIL_WATCH_LABEL_IDS_CSV=INBOX

# ── Recall AI ───────────────────────────────────────────────────
RECALL_AI_TOKEN=<your-recall-api-token>

# Region-specific base URL — change to match your Recall account region
# Options: us-east-1, eu-west-2, ap-northeast-1, etc.
RECALL_AI_BASE_URL=https://ap-northeast-1.recall.ai/api/v1

# Optional: display name shown for the bot inside the meeting
# RECALL_AI_BOT_NAME=Gemini Agent

# ── Gemini / ADK ────────────────────────────────────────────────
# Default model; override if you have access to a different preview
# DEMO_AGENT_MODEL=gemini-2.5-flash-native-audio-preview-12-2025
```

> All variable names map directly to the `Settings` class in [app/core/config.py](app/core/config.py).

---

## 5. Start the database

```bash
# Copy environment variables for Docker Compose
# (or export them directly; docker-compose.yaml reads POSTGRES_* vars)
docker compose up -d db
```

Wait until the container is healthy:

```bash
docker compose ps db
```

---

## 6. Run database migrations

```bash
uv run alembic upgrade head
```

This creates four tables: `gmail_history_state`, `recall_failure_queue`, `meeting_invite`.

To create a new migration after model changes:

```bash
uv run alembic revision --autogenerate -m "describe your change"
uv run alembic upgrade head
```

---

## 7. Bootstrap the Gmail watch

This step starts the Gmail push subscription and stores the baseline `historyId` in the database so incremental history queries work correctly. Run it once, and re-run it whenever the watch expires (~7 days) or after a reset.

```bash
uv run python -m app.integrations.google.watch
```

Expected output:
```json
{
  "emailAddress": "you@gmail.com",
  "historyId": "1234567",
  "expiration": "1234567890000"
}
```

---

## 8. Run the app

```bash
uv run uvicorn app.main:app --reload
```

The server starts on `http://localhost:8000`.

| URL | Description |
|-----|-------------|
| `http://localhost:8000/` | Live audio demo UI |
| `http://localhost:8000/dashboard` | Meeting invite dashboard |
| `http://localhost:8000/docs` | Interactive OpenAPI docs |

---

## API reference

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |

### Gmail webhook

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/gmail/webhook` | Receives Pub/Sub push notifications from Gmail |

### Meetings

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/meetings` | List all tracked meeting invites |

### Recall bot queue (manual review)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/recall/failures` | List failed Recall bot scheduling attempts |
| `POST` | `/api/recall/failures/{queue_id}/resolve` | Mark a failure as resolved |
| `PATCH` | `/api/recall/bots/{bot_id}` | Manually update a Recall bot |

### WebSocket

| Path | Description |
|------|-------------|
| `WS /ws/{user_id}/{session_id}` | Bidirectional audio stream to Gemini Live API via ADK |

The WebSocket accepts/sends JSON frames:

```jsonc
// client → server
{ "mime_type": "audio/pcm", "data": "<base64-encoded PCM>" }
{ "mime_type": "text/plain", "data": "Hello" }

// server → client
{ "mime_type": "audio/pcm", "data": "<base64-encoded PCM>" }
{ "mime_type": "text/plain", "data": "..." }
{ "turn_complete": true }
```

---

## Development

### Run tests

```bash
uv run pytest
```

### Project layout

```
app/
  main.py                  # FastAPI app, WebSocket endpoint
  core/config.py           # Typed settings (pydantic-settings)
  api/                     # REST API routers
  services/
    gmail/                 # Gmail history processing and parsing
    meetings/              # Meeting invite creation and scheduling
    recall/                # Recall failure queue management
    google_search_agent/   # ADK agent definition
  integrations/
    google/                # Gmail API client + watch bootstrap
    recall/                # Recall AI REST client
  web/                     # FastHTML dashboard and demo UI
  db/                      # SQLModel models and async session
alembic/                   # Database migration scripts
docs/                      # Product proposal and design notes
```

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

The main demo UI at `/`, the Recall runtime at `/recall`, and the FastHTML dashboard at `/dashboard/` now all load Tailwind CSS and daisyUI from CDN. That means you can use Tailwind utility classes and daisyUI component classes across the repo's frontend entrypoints without adding a Node build pipeline.

The `/` and `/recall` pages are now rendered from Python with FastHTML instead of serving template files. Their browser CSS/JS assets also moved out of `app/static` and now live under `app/web/assets`, served by the web router at `/assets/...`.

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