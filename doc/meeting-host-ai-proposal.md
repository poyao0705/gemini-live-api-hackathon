# Meeting Host AI Proposal

## Working Title
**Meeting Host AI**  
An AI-powered meeting host and secretary that uses voice to facilitate meetings, summarize discussions, capture decisions, and keep conversations focused.

---

## 1. Problem Statement

Meetings often suffer from:
- Too many participants being involved in topics that do not require them
- Long discussions without clear decisions
- Scope creep and off-topic conversation
- Poor accountability for action items and owners
- Lost context for late or passive attendees
- Inefficient communication between technical and non-technical stakeholders

This project proposes an AI meeting assistant that acts as a **silent, non-intrusive host** most of the time, and only intervenes when necessary to improve meeting quality and reduce wasted time.

---

## 2. Vision

Build a voice-enabled AI meeting assistant that can:
- Host meetings when needed
- Summarize discussion in real time
- Act as a secretary by capturing decisions and action items
- Help explain and rephrase technical or non-technical points
- Prevent scope creep by redirecting unrelated discussion
- Support lightweight participation from busy stakeholders
- Stay quiet unless intervention is useful and timely

---

## 3. Core Value Proposition

The AI should help teams:
- **Reduce meeting time**
- **Reduce the number of people needed in each discussion**
- **Improve clarity between technical and non-technical participants**
- **Capture decisions instantly**
- **Maintain accountability**
- **Keep meetings on-topic**
- **Support passive or asynchronous stakeholders**

---

## 4. Key Product Features

### 4.1 AI Voice Host and Secretary
The AI joins the meeting as a voice-enabled assistant that can:
- Open the meeting with agenda reminders
- Listen continuously
- Summarize key discussion points
- Record decisions, owners, and deadlines
- Produce post-meeting notes automatically

#### Example behavior
- “Here’s a quick summary of what has been discussed so far.”
- “Let me restate that in simpler terms.”
- “I’ve captured that as an action item.”

---

### 4.2 Scope Control / Focus Guard
The AI detects when the conversation drifts away from the current topic and gently redirects participants.

#### Example intervention
- “That sounds related but outside today’s scope. Shall I record it for a follow-up discussion and bring us back to the current topic?”

#### Goal
- Prevent scope creep
- Keep the meeting focused
- Avoid wasting time on unrelated topics

---

### 4.3 Technical / Non-Technical Explainer
The AI can translate language across audiences.

#### Examples
- Rephrase a technical explanation for business stakeholders
- Rephrase a business request into technical requirements
- Simplify jargon in real time

#### Goal
- Reduce misunderstanding
- Improve cross-functional communication
- Enable fewer people to attend while still maintaining shared understanding

---

### 4.4 Tension Radar / Room Pulse
The AI monitors meeting dynamics and surfaces a subtle “meeting health” signal based on:
- Crosstalk
- Long silences
- Raised voices or overlapping speech
- Signs of disagreement or confusion

It can intervene gently when needed.

#### Example intervention
- “It sounds like there are two competing ideas. Let me capture both options clearly.”
- “There’s been a long pause — would a quick summary help?”
- “It seems there may be some disagreement. Would you like me to outline the trade-offs?”

#### Goal
- Improve meeting flow
- Reduce unproductive friction
- Help teams recover from confusion without escalating tension

---

### 4.5 Instant Decision Capture with Accountability
When the AI detects that a decision is being made, it confirms the decision in real time and logs it visibly.

#### Example intervention
- “Just to confirm — the decision is X, owned by Y, due by [date]. Is that correct?”

#### The live decisions log should capture:
- Decision
- Owner
- Due date
- Context or rationale
- Status if needed

#### Goal
- Avoid ambiguity
- Improve accountability
- Turn spoken decisions into trackable outputs immediately

---

### 4.6 Polling / Lightweight Facilitation
The AI can facilitate quick polls when needed.

#### Use cases
- Resolve simple disagreements
- Check alignment before moving on
- Gather fast input from participants

#### Examples
- “Would you like me to run a quick vote on Option A vs Option B?”
- “I’m detecting split opinions. Shall I summarize the options and poll the room?”

---

### 4.7 Ghost Attendee Mode
Busy stakeholders can join as “ghost attendees.”

They do not actively speak in the meeting, but the AI:
- Summarizes the meeting for them live
- Accepts text-based questions from them
- Voices those questions at appropriate moments
- Reduces the need for them to attend fully and synchronously

#### Goal
- Keep stakeholders informed without requiring full participation
- Reduce interruptions
- Enable asynchronous or low-attention participation

---

### 4.8 Silent-by-Default Interaction Model
A key design principle is that the AI should be **non-intrusive**.

The AI should:
- Stay silent most of the time
- Only speak when confidence is high that intervention is helpful
- Use brief, low-friction prompts
- Avoid dominating the meeting
- Behave like a facilitator, not a participant

#### Trigger philosophy
The AI should only “jump in” when:
- A clear decision is forming
- Discussion goes off-topic
- Communication needs translation or clarification
- Tension or confusion becomes visible
- A ghost attendee has an important queued question
- A user explicitly asks for help

---

## 5. User Experience Principles

### 5.1 Non-Intrusive
- Silent by default
- Short interventions
- Soft tone
- Easy to mute or suppress

### 5.2 Helpful but Controlled
- Intervene only with clear value
- Avoid over-summarizing
- Avoid repeating obvious points
- Respect conversational flow

### 5.3 Visible Accountability
- Capture decisions and action items live
- Make logs visible to all participants

### 5.4 Inclusive Communication
- Bridge technical and non-technical language
- Support passive attendees
- Reduce confusion for all participants

---

## 6. Technical Challenges to Overcome

### 6.1 Speaker Identification
Challenge:
- Distinguishing between participants such as “Person A, B, C”
- Voice attribution becomes harder in multi-person settings

Proposed constraint:
- Limit supported meeting size to **up to 4 participants** initially

Possible mitigation:
- Require participant registration before the meeting
- Capture speaker profiles in advance
- Use hardware-assisted identity input in worst-case scenarios
- Provide fallback manual correction if speaker attribution is uncertain

---

### 6.2 Registration Before Meeting
Participants may need to register before the meeting:
- Name
- Role
- Voice sample or identity confirmation
- Meeting purpose or agenda relevance

Benefits:
- Better speaker recognition
- Better personalized summaries
- Better owner assignment for decisions and tasks

---

### 6.3 Hardware Touch Input Fallback
Worst-case fallback:
- Use a hardware touch input or simple participant device interaction to identify who is currently speaking or confirming an action

Use cases:
- Speaker identity correction
- Confirming decisions
- Marking ownership quickly

---

### 6.4 Controlling AI Talkativeness
A major technical and product challenge is making the AI **shut up most of the time**.

The system must include:
- Strong intervention thresholds
- Priority ranking for interruption events
- Time-based cooldowns between interventions
- User-configurable verbosity settings
- A “silent mode” with visual-only prompts
- Confidence scoring before speaking aloud

#### Success metric
Participants should feel:
- supported,
- not interrupted,
- and never overshadowed by the AI.

---

## 7. Proposed MVP Scope

### MVP Goals
Build a simple but compelling prototype that demonstrates the concept during the hackathon.

### In-Scope for MVP
- Live meeting listening
- Basic real-time summarization
- Decision detection and confirmation
- Action item capture with owner + due date
- Off-topic detection and gentle redirection
- Technical/non-technical rephrasing
- Ghost attendee text input with AI voice relay
- Support for up to 4 registered participants
- Silent-by-default intervention rules

### Out of Scope for MVP
- Large meetings
- Perfect speaker diarization in noisy rooms
- Deep enterprise integrations
- Full calendar/workspace ecosystem
- Advanced emotion analysis beyond simple meeting-health heuristics

---

## 8. Detailed Action Items

### 8.1 Product Definition
- Define primary user persona
- Define target meeting types
- Decide when AI should speak vs stay silent
- Define success metrics for “non-intrusive” behavior
- Finalize MVP feature list

### 8.2 Conversation Intelligence
- Build real-time transcription pipeline
- Detect decisions from natural conversation
- Detect action items, owners, and deadlines
- Detect off-topic discussion
- Detect requests for simplification or rephrasing
- Generate concise live summaries

### 8.3 Meeting Health / Tension Detection
- Detect overlapping speech
- Detect long silence periods
- Detect raised volume or repeated interruption patterns
- Convert these into a simple “room pulse” indicator
- Design subtle intervention prompts

### 8.4 Ghost Attendee Workflow
- Create ghost attendee mode
- Accept stakeholder text input
- Queue and prioritize questions
- Determine appropriate interruption timing
- Voice the question naturally through the AI host

### 8.5 Participant Identity / Registration
- Create pre-meeting registration flow
- Register participant names and roles
- Add optional voice enrollment
- Add manual correction flow for misidentified speakers
- Enforce initial participant cap of 4 people

### 8.6 AI Behavior Controls
- Create intervention threshold logic
- Add cooldown period between spoken interventions
- Add verbosity settings
- Add mute / visual-only mode
- Add confidence gating before spoken output

### 8.7 Decision Log / Meeting Notes UI
- Build live decisions panel
- Build action items panel
- Show owner and due date
- Show meeting summary in real time
- Support export as meeting notes after session ends

### 8.8 Demo Design
- Prepare a short demo scenario
- Include one off-topic redirect
- Include one technical-to-non-technical rephrase
- Include one decision capture moment
- Include one ghost attendee text question
- Include one meeting-health intervention
- End with an auto-generated summary

---

## 9. Suggested Demo Flow

1. Meeting starts with 3–4 participants
2. AI gives a short opening and agenda reminder
3. Participants discuss a feature or project topic
4. One speaker becomes too technical
5. AI rephrases for non-technical participants
6. Discussion drifts off-topic
7. AI redirects and offers to log the tangent for later
8. Team reaches a decision
9. AI confirms decision, owner, and due date
10. A ghost attendee sends a text question
11. AI voices the question at an appropriate time
12. Some overlap/confusion happens
13. AI surfaces a subtle room-pulse intervention
14. Meeting ends with instant summary, decisions, and action items

---

## 10. Success Criteria

The prototype is successful if it demonstrates that the AI can:
- Improve meeting focus
- Reduce unnecessary meeting participation
- Capture decisions accurately
- Help mixed technical/non-technical groups communicate better
- Support passive stakeholders
- Remain mostly silent and non-disruptive

---

## 11. Open Questions

- How should the AI decide when to speak aloud versus only update the UI?
- How accurate does speaker identification need to be for the MVP?
- What is the best way to signal tension without making users uncomfortable?
- How should ghost attendee questions be prioritized?
- How do we measure whether the AI is genuinely reducing meeting time?
- What intervention threshold makes the AI useful without becoming annoying?

---

## 12. One-Line Pitch

**A silent-by-default AI meeting host that keeps discussions focused, captures decisions instantly, bridges technical and non-technical communication, and enables lightweight participation for busy stakeholders.**

---

## 13. Hackathon Positioning

This idea is compelling for a Gemini Live API hackathon because it highlights:
- Real-time voice interaction
- Context-aware facilitation
- Live summarization
- Human-AI collaboration
- Practical workplace productivity gains

It is both:
- technically interesting, and
- easy to demonstrate with a realistic meeting scenario.

---
## 14. Recommended Next Step

Turn this proposal into:
1. a **hackathon pitch deck**,
2. an **MVP feature breakdown**, and
3. a **demo script** for judges.
