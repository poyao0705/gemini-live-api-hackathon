# MVP Feature Breakdown — Meeting Host AI

## Objective
Build a hackathon MVP that proves the core idea:

> An AI meeting host that stays quiet most of the time, intervenes only when useful, and helps teams keep meetings focused, understandable, and actionable.

The MVP should prioritize:
- clear live value,
- a realistic demo,
- low interaction friction,
- and strong “silent-by-default” behavior.

---

## 1. MVP Goals

### Primary goals
- Demonstrate real-time meeting listening
- Show concise AI interventions at the right moments
- Capture decisions and action items live
- Prevent scope creep
- Translate between technical and non-technical language
- Support one lightweight “ghost attendee”

### MVP success criteria
The MVP is successful if, during the demo, the AI can:
- summarize discussion accurately,
- redirect an off-topic tangent,
- confirm and log a decision,
- rephrase something complex in simpler language,
- relay a ghost attendee question,
- and avoid speaking too often.

---

## 2. Core MVP Features

## Feature 1: Live Meeting Transcription
### What it does
Continuously listens to the meeting and converts speech into text in real time.

### Why it matters
This is the foundation for all other intelligence:
- summary generation,
- decision detection,
- off-topic detection,
- rephrasing,
- and meeting-health monitoring.

### MVP requirements
- Real-time speech-to-text
- Speaker-separated transcript if possible
- Support up to 4 participants
- Display transcript in the UI

### Input
- Live voice from meeting participants

### Output
- Streaming transcript text
- Optional speaker labels

### Demo value
Lets judges see that the AI is actually following the conversation.

---

## Feature 2: Silent-by-Default AI Intervention Engine
### What it does
Determines when the AI should speak and when it should stay quiet.

### Why it matters
This is the product-defining feature. The AI should feel helpful, not annoying.

### MVP requirements
- AI does **not** speak continuously
- AI only intervenes on predefined trigger events
- Add cooldown between interventions
- Keep interventions short and low-friction

### Initial intervention triggers
- Decision detected
- Off-topic drift detected
- Explicit user request to summarize or explain
- Ghost attendee question ready
- Strong confusion / overlap pattern detected

### Intervention rules
- Max one spoken intervention within a short cooldown window
- If confidence is low, show UI suggestion instead of speaking
- Prefer visual update over voice unless interruption is valuable

### Demo value
Shows that the AI is designed as a facilitator, not as a dominant meeting participant.

---

## Feature 3: Real-Time Summary Panel
### What it does
Maintains a short rolling summary of the meeting as discussion evolves.

### Why it matters
Provides immediate value even when the AI is not speaking.

### MVP requirements
- Show “discussion so far” in concise bullets
- Refresh periodically
- Keep summary short and readable
- Highlight latest key point

### Output format
- 3–5 bullet summary
- updated every defined interval or after key events

### Demo value
Gives the audience a visible artifact of AI understanding.

---

## Feature 4: Decision Detection and Confirmation
### What it does
Detects when the conversation sounds like a decision is being made, then confirms it.

### Example trigger phrases
- “Let’s go with…”
- “We’ll do…”
- “Sounds good, let’s proceed with…”
- “Decision made…”
- “So the plan is…”

### AI behavior
The AI softly interrupts with something like:

> “Just to confirm — the decision is X, owned by Y, due by [date]. Is that correct?”

### MVP requirements
- Detect likely decision moments
- Extract decision statement
- Ask for confirmation
- Capture owner and due date if mentioned
- Add confirmed decision to live log

### Output
- Decision
- Owner
- Due date
- Status: pending confirmation / confirmed

### Demo value
This is one of the strongest “wow” moments.

---

## Feature 5: Action Item Capture
### What it does
Extracts follow-up tasks from the conversation.

### Example trigger phrases
- “I’ll handle that”
- “Can you send that tomorrow?”
- “Let’s follow up next week”
- “You take frontend, I’ll do backend”

### MVP requirements
- Detect action-oriented statements
- Extract owner if available
- Extract due date if available
- Show them in a live task panel

### Output
- Action item
- Owner
- Due date
- Confidence or confirmation state

### Demo value
Shows clear practical utility beyond summarization.

---

## Feature 6: Scope Creep / Off-Topic Detection
### What it does
Detects when discussion is drifting away from the active meeting topic and gently redirects it.

### Example AI intervention
> “That seems related but outside the current topic. Would you like me to log it for follow-up and bring us back to today’s discussion?”

### MVP requirements
- Set a meeting topic or agenda at the beginning
- Compare ongoing discussion against current scope
- Detect tangent/off-topic segments
- Offer to park the tangent instead of fully blocking it

### Output
- Off-topic flag
- Suggested intervention
- “Parking lot” item added to side list

### Demo value
Directly supports the promise of reducing wasted meeting time.

---

## Feature 7: Technical / Non-Technical Rephrase
### What it does
Rewrites a spoken explanation into a more technical or more non-technical version.

### Use cases
- Engineer explains system architecture to product manager
- Product stakeholder gives vague business request that needs technical framing

### MVP requirements
- Manual trigger or phrase trigger:
  - “Can you simplify that?”
  - “Can you rephrase that for non-technical people?”
- Generate concise rephrased explanation
- Display in UI and optionally speak it

### Output
- Original concept
- Rephrased explanation
- Mode: technical → simple, or business → technical

### Demo value
Easy to understand and very impressive in a live demo.

---

## Feature 8: Ghost Attendee Mode
### What it does
Allows one passive stakeholder to follow the meeting without actively speaking.

### MVP behavior
- Ghost attendee receives live summary
- Ghost attendee submits one or more text questions
- AI injects the question at an appropriate moment

### Example AI behavior
> “A ghost attendee has a question: what is the expected launch timeline?”

### MVP requirements
- One ghost attendee supported
- Simple text input interface
- Queue questions
- AI chooses a non-disruptive insertion point

### Demo value
Shows a unique interaction model and differentiates the product.

---

## Feature 9: Meeting Health / Room Pulse Indicator
### What it does
Shows a lightweight signal for meeting quality based on simple conversational patterns.

### Signals to detect
- Frequent interruption / overlap
- Long silence
- Rapid back-and-forth disagreement
- Possible confusion

### MVP requirements
- Simple heuristic-based score or status:
  - Healthy
  - Slight tension
  - Confused / fragmented
- Optional subtle intervention from AI

### Example intervention
> “It sounds like there are two competing ideas — let me summarize both.”

### Demo value
Adds emotional and facilitation intelligence without needing full sentiment analysis.

---

## Feature 10: Live Meeting Log UI
### What it does
Displays the AI’s outputs in one simple interface.

### MVP sections
- Live transcript
- Rolling summary
- Decisions log
- Action items
- Parking lot / off-topic items
- Ghost attendee question queue
- Meeting health status

### Why it matters
Even if voice output is limited, the UI makes the AI’s value visible.

### Demo value
Makes the system understandable instantly for judges.

---

## 3. MVP Feature Prioritization

## Tier 1 — Must Have
These are essential for the MVP demo.

1. Live transcription  
2. Silent-by-default intervention logic  
3. Rolling summary panel  
4. Decision detection + confirmation  
5. Action item capture  
6. Off-topic detection / parking lot  
7. Simple live meeting log UI  

---

## Tier 2 — Strong Should Have
These features make the demo significantly better.

1. Technical / non-technical rephrase  
2. Ghost attendee mode  
3. Basic meeting health indicator  

---

## Tier 3 — Nice to Have
Only build if time remains.

1. Speaker registration flow  
2. Speaker identification by person name  
3. Due-date extraction improvements  
4. Verbosity settings  
5. Visual-only mode toggle  
6. Polling support  

---

## 4. Suggested Implementation Strategy

## Track A: Input / Understanding
Build the pipeline that converts live speech into structured meeting signals.

### Tasks
- Capture microphone audio
- Stream speech-to-text
- Chunk transcript into segments
- Send transcript windows to LLM prompts
- Classify:
  - summary update,
  - decision signal,
  - action item signal,
  - off-topic signal,
  - rephrase request,
  - tension signal

---

## Track B: Intervention Logic
Build the rules for when the AI should speak.

### Tasks
- Define trigger event types
- Add confidence score threshold
- Add cooldown timer
- Define spoken vs UI-only behavior
- Create short intervention templates

### Example policy
- Decision detection: speak
- Off-topic tangent: speak once, then quiet
- Summary update: UI only by default
- Low-confidence action item: UI only
- Ghost question: speak when pause detected

---

## Track C: UI / Demo Experience
Build a single-page interface for the live meeting.

### Tasks
- Transcript panel
- Summary panel
- Decisions log
- Action items list
- Parking lot section
- Health indicator
- Ghost attendee text input

---

## Track D: Demo Scripting
Build for the demo, not for full generality.

### Tasks
- Prepare a sample meeting topic
- Prepare scripted moments for:
  - off-topic drift,
  - technical jargon,
  - final decision,
  - ghost attendee question,
  - mild tension/overlap
- Tune prompts around expected inputs

---

## 5. Detailed Action Items by Feature

## A. Live Transcription
- Select audio input method
- Connect streaming transcription
- Display transcript in UI
- Break transcript into time windows for downstream analysis

## B. Summary Engine
- Create summary prompt
- Update rolling summary every N seconds or after key events
- Limit summary to 3–5 bullets
- Highlight the newest bullet

## C. Decision Detection
- Define decision phrases and semantic patterns
- Extract decision statement
- Ask for confirmation
- Add decision to log after confirmation

## D. Action Item Extraction
- Define task-oriented phrases
- Extract owner names
- Extract due dates when present
- Add to action panel

## E. Off-Topic Detection
- Accept meeting agenda or topic as initial context
- Compare current discussion chunk against agenda
- Detect likely tangents
- Add tangent to parking lot
- Trigger gentle redirect

## F. Rephrase Feature
- Add button or voice command trigger
- Support:
  - simplify this
  - explain for non-technical audience
  - convert to technical summary
- Show rephrased result in UI

## G. Ghost Attendee
- Build ghost text input
- Queue text questions
- Create “best time to inject” logic
- Voice the selected question

## H. Room Pulse
- Track overlap frequency
- Track silence duration
- Track disagreement markers
- Convert to a simple status label
- Optionally trigger one intervention

## I. AI Talkativeness Controls
- Add spoken intervention cooldown
- Add max interventions per meeting segment
- Add confidence threshold
- Prefer UI updates unless speaking is necessary

---

## 6. Data Structures for MVP

### Decision item
- id
- timestamp
- decision_text
- owner
- due_date
- status
- confidence

### Action item
- id
- timestamp
- task_text
- owner
- due_date
- confidence

### Parking lot item
- id
- timestamp
- tangent_text
- related_topic

### Summary item
- id
- timestamp
- bullet_text

### Ghost question
- id
- submitted_at
- question_text
- status

---

## 7. Recommended Hackathon Scope Cut

If time is tight, cut down to this minimum demoable slice:

### Minimum viable demo
- Live transcription
- Rolling summary
- One decision detection flow
- One action item extraction
- One off-topic redirect
- One technical/non-technical rephrase
- One ghost attendee question
- One simple UI dashboard

This is enough to demonstrate the full concept clearly.

---

## 8. Demo Script Mapping to Features

### Demo moment 1: Normal discussion
Shows:
- transcription
- rolling summary

### Demo moment 2: Technical jargon appears
Shows:
- rephrase feature

### Demo moment 3: Topic drift
Shows:
- off-topic detection
- parking lot
- gentle redirect

### Demo moment 4: Team agrees on a plan
Shows:
- decision detection
- confirmation
- live decision log

### Demo moment 5: Someone volunteers a follow-up
Shows:
- action item extraction

### Demo moment 6: Ghost attendee sends text
Shows:
- ghost attendee mode
- timed AI insertion

### Demo moment 7: Mild confusion / overlap
Shows:
- room pulse indicator
- subtle facilitation prompt

### Demo moment 8: Meeting ends
Shows:
- final summary
- decisions
- action items
- parking lot export

---

## 9. Team Task Breakdown

## Product / Prompt Design
- Define intervention rules
- Define prompt templates
- Define summary style
- Define rephrase style
- Define decision confirmation format

## Frontend
- Build live dashboard
- Build transcript and log components
- Build ghost attendee input
- Build health indicator

## Backend / Realtime
- Audio ingestion
- Transcript streaming
- Event detection pipeline
- LLM orchestration
- State management for meeting artifacts

## Demo / QA
- Create scripted sample conversation
- Test timing of interventions
- Tune non-intrusive behavior
- Validate final summary accuracy

---

## 10. Final MVP Statement

The MVP is not trying to solve every meeting problem.

It is trying to prove one clear idea:

> A quiet AI facilitator can listen to a live conversation, step in only when useful, and produce immediate meeting value through summaries, focus control, decision capture, and lightweight participation support.
