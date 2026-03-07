# gemini-live-api-hackathon
Live API hackathon

- To run in local, please run: `uv run uvicorn app.main:app --reload `

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