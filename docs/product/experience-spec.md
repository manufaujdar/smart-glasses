# Clinical smart-glasses experience specification

## Experience loop

`invoke → identify context → preview action → confirm → execute → acknowledge → audit`

## Core modes

- **Ready:** connected, no patient and no recording.
- **Encounter:** explicit patient/encounter context with a visible expiry.
- **Capture:** visible camera/audio state with elapsed time and stop control.
- **Consult:** encrypted live media with participant and recording state.
- **Review:** media/draft is local and has not entered the clinical record.
- **Degraded:** network/model/integration unavailable; permitted local actions only.
- **Clear:** all optional overlays/audio prompts suppressed immediately.

## First three prototype experiences

### 1. Structured procedure note

Press/voice starts an audio note, the phone transcribes locally or through an approved service, and a structured draft is shown on the phone. The clinician edits and approves; the prototype exports JSON rather than writing to an EHR.

### 2. First-person remote consult

The clinician initiates a named session and receives a clear join acknowledgement. Remote annotations are advisory and never obscure the central view. Network loss terminates guidance visibly.

### 3. Visual reference capture

The clinician captures a scene, reviews it on the phone, and chooses delete, retain locally, or send to an approved workflow. The default is delete after the test session.

## Non-negotiable UX rules

- no always-on recording in the prototype
- no hidden background capture
- no patient identification from face recognition
- no clinical output without source/time or draft status
- no automatic record write
- physical or phone stop always overrides voice/AI
- no diagnostic or surgical-navigation claim

