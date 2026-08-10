# Surgeon-facing validation plan

## Test levels

| Level | Data/environment | Purpose |
|---|---|---|
| automated | synthetic IDs and events | state transitions, gates, safe-stop and audit |
| bench | test patterns and staged objects | latency, battery, heat, capture/transfer and faults |
| simulation lab | mannequin and representative OR team | distraction, PPE, voice, controls and workflow fit |
| security/privacy | synthetic traffic and adversarial inputs | authorization, leakage, retention and recovery |
| clinical feasibility | only under approved protocol | bounded intended-use feasibility and human factors |

## Required scenario families

- missing preflight item cannot arm the session
- low battery, missing capture indicator or missing capability blocks readiness
- device disconnect stops recording/streaming and suppresses display content
- network loss cannot leave stale remote annotation visible
- clear-view works during recording, streaming and model delay
- consent/policy expiry stops affected functions and requires explicit re-authorization
- wrong-session switch requires explicit confirmation and closes prior media state
- crash/restart does not silently resume recording, streaming or overlay
- every command/result pair is correlated without media or PHI in logs

## Human-factors outcomes

Measure critical-task errors, time on task, missed checklist/team communication,
unintended activation, successful stop/clear-view, visual occlusion, workload,
discomfort, thermal sensation and recovery from faults. Define acceptance criteria and
stop rules before testing; do not reinterpret them after results are known.

