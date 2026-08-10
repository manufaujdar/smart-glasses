# Human factors, safety and governance

## OR-specific hazards and initial controls

| Hazard | Initial control | Verification |
|---|---|---|
| visual obstruction or distraction | central field remains clear; bounded cards; physical/phone clear-view | simulated critical-task test |
| wrong session or patient context | explicit context, expiry and two-step switch; synthetic IDs in development | state and usability tests |
| covert or unintended recording | explicit authorization, visible indicator, audible acknowledgement and local stop | 100-cycle capture test |
| remote mentor mistaken for authority | named participant, advisory label and immediate disconnect | scenario test |
| delayed or stale AI output | source time, latency, expiry and automatic suppression | fault-injection test |
| network/device loss during session | local safe-stop; capture and stream false; overlays off | disconnect test |
| sterility or PPE interference | no touch requirement in sterile field; cleaning and compatibility study | simulation-lab protocol |
| battery/thermal discomfort | preflight threshold, thermal monitoring and stop rule | bench and wear test |
| PHI disclosure | data minimization, encryption, named destination, retention and audit policy | privacy/security review |
| prompt or scene injection | treat video/text/audio as untrusted; bounded tools and confirmation | adversarial test |

## Safety hierarchy

1. Remove unnecessary features and data.
2. Prevent unsafe states through hard gates and least privilege.
3. Detect faults and degrade to a clear, non-guiding state.
4. Inform the operator through simple, unambiguous status.
5. Validate with representative users and environments.

Warnings alone are not an adequate control for a foreseeable high-severity hazard.

## Governance gates before real-world use

- named clinical owner and intended-use statement
- privacy impact assessment and informed recording/streaming process
- infection-control and biomedical-engineering approval
- cybersecurity review, SBOM and dependency provenance
- hazard log with risk-control verification and residual-risk approval
- representative human-factors study and stop rules
- institutional ethics/IRB determination where applicable
- regulatory classification advice for each jurisdiction
- incident, rollback, retention and model-change procedures

The WHO checklist is a team communication process. A glasses prototype may display
locally approved prompts, but it must not silently mark items complete or replace
verbal confirmation by the surgical team.

## Authoritative starting points

- WHO Surgical Safety Checklist tools: https://www.who.int/teams/integrated-health-services/quality-of-care-and-patient-safety/patient-safety-guidance-and-tools/safe-surgery/tool-and-resources
- FDA Medical Device Software Guidance Navigator: https://www.fda.gov/medical-devices/regulatory-accelerator/medical-device-software-guidance-navigator
- FDA human factors overview: https://www.fda.gov/medical-devices/device-advice-comprehensive-regulatory-assistance/human-factors-and-medical-devices

These are starting points, not a jurisdiction-specific regulatory determination.

