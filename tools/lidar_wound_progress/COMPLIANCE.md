# Local healthcare-safeguard baseline

This project is research software and is not HIPAA-certified, GDPR-certified,
FDA-cleared, or approved for production clinical use. Compliance depends on the
organization, jurisdiction, intended use, data, contracts, and operating
environment. A legal/privacy/security owner must review any use with real
patient data.

## Implemented prototype safeguards

- Data minimization: the webapp stores numeric summaries only; camera stills
  remain in memory and raw depth grids are not sent to the local store.
- Local-first persistence: browser `localStorage` is available without a
  server; the optional Python service binds to loopback and stores summaries in
  SQLite.
- Input validation: bounded JSON bodies, opaque identifier formats, finite
  measurements, timezone-aware timestamps, allow-listed sensor modes, and
  rejection of image/depth-grid fields in the SQLite API.
- Auditability: local record save/delete events are written to a minimal audit
  table without storing clinical narrative or direct identifiers.
- Access boundary: the service refuses non-loopback hosts by default and can
  require `DEPTHLINE_LOCAL_TOKEN` for local API requests.
- Deletion/export: the browser supports clearing local history and downloading
  the current numeric record; the local service exposes record deletion.

## Required before any PHI or clinical deployment

1. Define intended use, data classification, retention, consent/authorization,
   role-based access, and incident response with the responsible organization.
2. Perform a documented security and privacy risk analysis; HHS describes HIPAA
   Security Rule safeguards as administrative, physical, and technical controls.
3. Use approved encryption at rest and in transit, managed identity, key
   rotation, backups, recovery testing, secure logging, vulnerability scanning,
   and least-privilege access. SQLite alone is not encryption at rest.
4. Establish minimum-necessary data handling, de-identification or limited data
   set rules, audit review, deletion/retention controls, and any required BAA,
   DPA, IRB, or institutional approvals.
5. Validate calibration, repeatability, segmentation/registration, sensor
   interchangeability, missing-data behavior, and demographic/setting
   robustness against an appropriate reference method.
6. Complete a clinical safety and regulatory assessment before describing any
   output as a wound score, healing assessment, or treatment-support function.

Useful external guidance:

- HHS [Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- HHS [Minimum Necessary Requirement](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/minimum-necessary-requirement/index.html)
- OWASP [Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/)
