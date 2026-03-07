# Meeting Host AI — Proposal, MVP Breakdown, and Technical Approach

## Working Title
**Meeting Host AI**  
A silent-by-default AI meeting co-host and secretary that listens to meetings, keeps discussions focused, captures decisions and action items, and helps technical and non-technical participants stay aligned.

---

# 1. Executive Summary

Meetings are often inefficient because they drift off-topic, include unnecessary participants, end without clear decisions, and create poor follow-through on action items.

This project proposes an **AI meeting co-host** that joins a meeting, listens in real time, summarizes discussion, detects decisions and tasks, and intervenes only when useful. Its goal is not to dominate the conversation, but to act like a **quiet facilitator and secretary**.

The product is designed to:
- reduce meeting time,
- reduce unnecessary participation,
- improve clarity between technical and non-technical people,
- prevent scope creep,
- capture decisions live,
- and support passive stakeholders through a “ghost attendee” mode.

For the hackathon MVP, the AI should be framed as a **silent co-host and secretary**, not a fully autonomous meeting host.

---

# 2. Problem Statement

Meetings commonly suffer from:
- too many people being pulled into discussions they do not need to attend,
- technical and non-technical participants talking past each other,
- off-topic tangents and scope creep,
- unclear decisions,
- weak accountability for next steps,
- and poor support for stakeholders who want updates without active participation.

Teams need a meeting assistant that can quietly support the conversation and improve meeting quality without becoming intrusive.

---

# 3. Product Vision

Build a voice-enabled AI meeting assistant that can:
- listen to meetings in real time,
- summarize what is being discussed,
- capture decisions and action items,
- help rephrase technical or non-technical explanations,
- redirect off-topic discussion,
- relay questions from passive stakeholders,
- and remain silent unless intervention is likely to be helpful.

The key product principle is:

> **Silent by default. Helpful when needed.**

---

# 4. Core Value Proposition

The AI should help teams:
- **reduce meeting time**
- **reduce the number of people needed in each discussion**
- **improve technical/non-technical communication**
- **capture decisions instantly**
- **maintain accountability**
- **keep meetings on topic**
- **support passive or asynchronous stakeholders**

---

# 5. Key Product Features

## 5.1 AI Voice Co-Host and Secretary
The AI joins a meeting as a facilitation layer that can:
- give agenda reminders,
- listen continuously,
- produce summaries,
- capture decisions,
- log action items,
- and generate post-meeting notes.

### Example behaviors
- “Here’s a quick summary of what has been discussed so far.”
- “Let me restate that in simpler terms.”
- “I’ve captured that as an action item.”

---

## 5.2 Scope Control / Focus Guard
The AI detects when discussion drifts away from the current topic and gently redirects the group.

### Example intervention
> “That seems related but outside today’s scope. Should I log it for follow-up and bring us back to the current topic?”

### Value
- prevents scope creep,
- keeps the meeting focused,
- and reduces wasted time.

---

## 5.3 Technical / Non-Technical Explainer
The AI helps bridge communication gaps by rephrasing content for different audiences.

### Example use cases
- simplify a technical explanation for business stakeholders,
- convert a business request into technical language,
- explain jargon in plain language.

### Value
- improves shared understanding,
- reduces confusion,
- and lowers the need for extra attendees just to translate context.

---

## 5.4 Tension Radar / Room Pulse
The AI monitors meeting flow and generates a subtle “meeting health” signal based on:
- overlapping speech,
- long silences,
- repeated interruption,
- or signs of disagreement/confusion.

### Example intervention
> “It sounds like there are two competing ideas. Let me summarize both clearly.”

### Value
- improves meeting flow,
- reduces unproductive friction,
- and helps the room recover from confusion.

---

## 5.5 Instant Decision Capture with Accountability
When the AI detects a likely decision, it confirms and logs it.

### Example intervention
> “Just to confirm — the decision is X, owned by Y, due by [date]. Is that correct?”

### Live decisions log
Each decision entry should include:
- decision text,
- owner,
- due date,
- optional rationale,
- and confirmation state.

### Value
- reduces ambiguity,
- increases accountability,
- and turns spoken decisions into shared artifacts immediately.

---

## 5.6 Polling / Lightweight Facilitation
The AI can help resolve simple disagreements by running lightweight polls.

### Example use cases
- choosing between two options,
- checking alignment,
- confirming group preference quickly.

### Example prompts
- “Would you like me to run a quick vote on Option A versus Option B?”
- “I’m detecting split opinions. Should I summarize both options and poll the group?”

---

## 5.7 Ghost Attendee Mode
Busy stakeholders can join passively as “ghost attendees.”

They do not actively speak in the meeting, but the AI can:
- keep them updated with live summaries,
- accept their text questions,
- and voice those questions at an appropriate moment.

### Value
- reduces the need for stakeholders to join actively,
- supports low-attention participation,
- and improves access to important meeting context.

---

## 5.8 Silent-by-Default Interaction Model
A defining principle of the product is that the AI should be **non-intrusive**.

The AI should:
- stay silent most of the time,
- speak only when the signal is strong,
- use short interventions,
- avoid repeating obvious information,
- and behave like a facilitator, not a participant.

### Trigger philosophy
The AI should only interrupt when:
- a decision is forming,
- the meeting goes off-topic,
- a clarification or rephrase is requested,
- confusion or tension is increasing,
- or a ghost attendee question should be injected.

---

# 6. MVP Positioning

For the hackathon MVP, do **not** position this as:

> “An AI that fully hosts the whole meeting autonomously.”

Instead position it as:

> **A silent AI co-host and secretary that intervenes only when useful.**

That framing is more believable, more demoable, and lower risk.

---

# 7. MVP Goals

The MVP should prove that the AI can:
- listen to a live meeting,
- maintain a short rolling summary,
- detect likely decisions,
- detect likely action items,
- redirect off-topic tangents,
- rephrase technical language,
- support one ghost attendee,
- and remain mostly silent.

### MVP success criteria
The MVP is successful if, in a demo, the AI can:
- summarize discussion accurately,
- redirect one tangent,
- confirm one decision,
- log one action item,
- rephrase one technical explanation,
- relay one ghost attendee question,
- and avoid becoming annoying.

---

# 8. Core MVP Features

## Feature 1: Live Meeting Transcription
### What it does
Continuously converts live speech into text.

### Why it matters
This is the foundation for:
- summary generation,
- decision detection,
- action item extraction,
- off-topic detection,
- and meeting health monitoring.

### MVP requirements
- real-time speech-to-text,
- transcript shown in UI.

### Output
- streaming transcript text

---

## Feature 2: Silent-by-Default Intervention Engine
### What it does
Controls whether the AI should speak or stay quiet.

### MVP requirements
- predefined trigger events,
- cooldown between spoken interventions,
- confidence threshold,
- preference for visual output when speech is unnecessary.

### Trigger events
- decision detected,
- off-topic drift,
- user asks for explanation or summary,
- ghost attendee question ready,
- confusion/overlap pattern detected.

---

## Feature 3: Rolling Summary Panel
### What it does
Maintains a concise “discussion so far” summary.

### MVP requirements
- 3–5 short bullet points,
- periodic refresh,
- latest key update highlighted.

---

## Feature 4: Decision Detection and Confirmation
### What it does
Detects likely decisions and confirms them.

### Example phrases
- “Let’s go with…”
- “We’ll do…”
- “So the plan is…”
- “Sounds good, let’s proceed with…”

### Expected output
- decision text,
- owner if mentioned,
- due date if mentioned,
- confirmation state.

---

## Feature 5: Action Item Capture
### What it does
Detects follow-up tasks from conversation.

### Example phrases
- “I’ll handle that”
- “Can you send that tomorrow?”
- “Let’s follow up next week”

### MVP behavior
- capture task text,
- capture owner if explicitly mentioned,
- capture due date if explicitly mentioned,
- ask for clarification when uncertain.

---

## Feature 6: Off-Topic Detection / Parking Lot
### What it does
Detects discussion drift and offers to park tangents.

### Example intervention
> “That seems outside the current topic. Should I log it for follow-up and bring us back?”

### Output
- off-topic flag,
- suggested redirect,
- parking lot item.

---

## Feature 7: Technical / Non-Technical Rephrase
### What it does
Rephrases content for a different audience.

### Triggers
- manual UI button,
- explicit request such as “simplify that” or “explain that for non-technical people.”

---

## Feature 8: Ghost Attendee Mode
### What it does
Lets one stakeholder follow passively and ask questions by text.

### MVP requirements
- one ghost attendee,
- simple text input,
- queued question injection at a low-disruption moment.

---

## Feature 9: Meeting Health / Room Pulse
### What it does
Shows a simple health indicator based on:
- overlap,
- long silence,
- repeated interruption,
- possible confusion.

### Output examples
- Healthy
- Slight tension
- Fragmented / confused

---

## Feature 10: Live Meeting Log UI
### What it does
Displays the AI’s outputs in one place.

### MVP UI sections
- transcript,
- rolling summary,
- decisions log,
- action items,
- parking lot,
- room pulse,
- ghost attendee queue.

---

# 9. MVP Prioritization

## Tier 1 — Must Have
1. Live transcription  
2. Silent-by-default intervention logic  
3. Rolling summary  
4. Decision detection + confirmation  
5. Action item capture  
6. Off-topic detection / parking lot  
7. Simple dashboard UI  

## Tier 2 — Strong Should Have
1. Technical / non-technical rephrase  
2. Ghost attendee mode  
3. Basic room pulse indicator  

## Tier 3 — Nice to Have
1. Registration flow  
2. Verbosity settings  
3. Visual-only mode  
4. Polling support  
5. Better due-date extraction  

---

# 10. Technical Discussion: Two Possible Implementations

## Option 1: Join a Normal Zoom Meeting
This is the more product-like version.

For this path, the important consideration is that Zoom’s Meeting SDK is intended for human meeting experiences, while realtime meeting-data use cases such as AI assistants and notetakers are directed toward **Realtime Media Streams (RTMS)** instead. RTMS is designed to provide access to live meeting media, transcript data, and participant-related events. ([developers.zoom.us](https://developers.zoom.us/docs/rtms/event-reference/?ampDeviceId=0134dd10-6975-48c7-b241-f38973aa1223&ampSessionId=undefined&utm_source=openai))

### High-level architecture
```text
Zoom meeting
   ↓
Zoom RTMS
   ↓
Backend (Node.js or Python)
   ↓
Realtime transcript / media processing
   ↓
LLM logic
   ↓
Outputs:
- summary
- decision log
- action items
- off-topic alerts
- ghost attendee relay
```

### Recommended MVP behavior
For the hackathon, the AI does **not** need to be a fully speaking avatar.

The better first version is a **silent meeting assistant** that:
- listens,
- processes transcript/audio,
- detects decisions/tasks/tangents,
- updates a side dashboard,
- optionally posts short prompts,
- and speaks only in limited cases.

### Minimal backend loop
```text
1. Zoom sends live media / transcript events
2. Backend buffers a short transcript window
3. Run lightweight detectors:
   - decision?
   - action item?
   - off-topic drift?
   - rephrase request?
4. If triggered, generate a short intervention
5. Deliver intervention to:
   - dashboard
   - meeting chat
   - optional TTS layer
```

### Best implementation sequence
#### Phase A — Silent secretary
- join meeting
- receive transcript/media stream
- produce live summary
- capture decisions and action items

#### Phase B — Low-frequency intervention
- off-topic redirect
- decision confirmation
- simplification / rephrasing

#### Phase C — Voice output
- convert selected interventions to speech
- enforce cooldown such as 60–90 seconds between spoken interruptions unless explicitly requested

---

## Option 2: Build Your Own Zoom-like Meeting Experience
This is more controllable but broader in scope.

Zoom’s Video SDK is intended for building custom real-time video experiences and supports capabilities such as chat and other realtime meeting controls; Zoom documentation and related materials also point developers toward building custom meeting UX with the Video SDK rather than repurposing the standard Meeting SDK for nonstandard automation scenarios. ([developers.zoom.us](https://developers.zoom.us/docs/video-sdk/web/chat/?ampDeviceId=cfb20154-f723-418e-a0a4-d2651410d5ef&ampSessionId=undefined&utm_source=openai))

### This option is better if you want
- full custom meeting UI,
- tighter control over intervention UX,
- built-in decision log / ghost attendee UX,
- easier participant metadata mapping.

### Tradeoff
For a hackathon, this is often too much to build unless the team is strong in realtime frontend and backend infrastructure.

---

# 11. Recommended Architecture for This Hackathon

The best MVP architecture is:

- **Zoom meeting** as the meeting surface
- **Zoom RTMS** for live meeting data
- **Python/FastAPI backend** for orchestration
- **Gemini Live or another realtime STT/LLM layer** for reasoning
- **React / Next.js dashboard** for:
  - rolling summary
  - decisions
  - action items
  - parking lot
  - room pulse
  - ghost attendee queue

This architecture aligns well with the product goal of event-driven meeting assistance.

---

# 12. Backend Component Breakdown

## A. Meeting Ingest Service
Receives Zoom live data and normalizes it.

### Responsibilities
- authenticate with Zoom,
- subscribe to RTMS,
- normalize incoming meeting events.

### Example event shape
```json
{
  "timestamp": "2026-03-07T14:03:21Z",
  "type": "transcript_chunk",
  "speaker": "unknown",
  "text": "I think we should ship option B next week"
}
```

---

## B. Realtime State Manager
Maintains rolling meeting memory.

### Tracks
- recent transcript window,
- current active topic,
- recent decisions,
- pending action items,
- recent interventions / cooldown state.

### Example state
```json
{
  "topic": "release scope for sprint 4",
  "last_intervention_at": "2026-03-07T14:02:10Z",
  "recent_candidates": [
    { "kind": "decision", "text": "ship option B next week" }
  ]
}
```

---

## C. LLM Orchestration Layer
Uses multiple narrow prompts instead of one giant prompt.

### Separate prompts/functions
- summarization,
- decision detection,
- action item extraction,
- off-topic detection,
- simplification / rephrasing,
- intervention recommendation.

This is more stable than one overloaded prompt.

---

## D. Delivery Layer
Sends outputs to:
- dashboard UI,
- meeting chat,
- optional TTS speech channel.

For MVP:
- **dashboard first**
- **voice second**

---

# 13. Core Detection Logic

## Decision Detector
Look for patterns like:
- “let’s do X”
- “we’ll go with Y”
- “agreed”
- “the decision is…”

### Example output
```json
{
  "kind": "decision",
  "decision": "Proceed with Option B",
  "confidence": 0.87,
  "needs_confirmation": true
}
```

---

## Action Item Extractor
Look for:
- task,
- owner,
- deadline.

### Example output
```json
{
  "kind": "action_item",
  "owner": null,
  "task": "Prepare prototype",
  "deadline": "Tuesday",
  "needs_owner_confirmation": true
}
```

---

## Off-Topic Detector
Compare the recent transcript window against:
- meeting title,
- agenda,
- active topic.

### Example output
```json
{
  "kind": "off_topic",
  "reason": "Conversation shifted from sprint scope to office seating",
  "confidence": 0.79
}
```

---

## Intervention Policy
The AI should **not** react to every signal.

### Example rules
```text
Speak only if:
- confidence > threshold
- no spoken intervention in last 75 seconds
- same issue persisted long enough
- message can be delivered briefly
```

This intervention policy is one of the most important product behaviors.

---

# 14. Output Modes

## Level 1 — Dashboard Only
Safest and easiest for MVP.

## Level 2 — Meeting Chat
Post prompts such as:
- “Possible decision detected: Use Option B. Confirm?”
- “Possible tangent detected. Return to release scope?”

## Level 3 — Full Agent Voice
Use TTS to inject audio into the meeting.

### Recommendation
For the hackathon, do not lead with full voice unless it is already stable. A bad voice interruption hurts the demo more than a text panel does.

---

# 15. Biggest Technical Risk

The biggest technical risk is **not** connecting to the meeting.

The biggest risk is:

> **intervening at the right time without becoming annoying.**

So the product should optimize for:
- short messages,
- low-frequency interruption,
- confirmation instead of authority,
- dashboard-first UX.

---

# 16. Speaker Identity Decision

For this project, **speaker identity is not a current MVP requirement**.

The MVP does **not** need strong participant attribution to prove value.

The core value can already be demonstrated through:
- summarization,
- decision capture,
- action item detection,
- off-topic control,
- ghost attendee support,
- and non-intrusive intervention.

When ownership is unclear, the AI can simply ask:
- “Who owns this task?”
- “Should I assign this decision to someone?”

This is sufficient for the MVP.

---

# 17. Future Improvements

Potential future enhancements include:
- speaker identification,
- participant attribution in notes,
- more reliable owner detection,
- support for larger meetings,
- stronger diarization in noisy settings,
- more advanced tension analysis,
- richer polling and facilitation features,
- and deeper enterprise integrations.

---

# 18. Recommended Hackathon Scope

If time is tight, build this exact slice:

## Minimum demoable version
- live transcription
- rolling summary
- one decision detection flow
- one action item capture
- one off-topic redirect
- one technical-to-non-technical rephrase
- one ghost attendee question
- one dashboard UI

That is enough to prove the concept well.

---

# 19. Demo Flow

1. Meeting starts
2. AI gives a short opening / agenda reminder
3. Participants discuss a topic
4. Technical jargon appears
5. AI rephrases it simply
6. Discussion drifts off-topic
7. AI offers to park the tangent
8. Team reaches a decision
9. AI confirms and logs it
10. One action item is captured
11. Ghost attendee sends a text question
12. AI injects it at a good moment
13. Mild overlap/confusion happens
14. AI surfaces room pulse and short facilitation prompt
15. Meeting ends with summary, decisions, and action items

---

# 20. Final Pitch

**Meeting Host AI is a silent-by-default AI co-host and secretary that listens to meetings, keeps discussions focused, captures decisions and action items in real time, bridges technical and non-technical communication, and supports passive stakeholders through lightweight participation.**