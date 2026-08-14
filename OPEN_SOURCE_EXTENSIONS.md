# Open-source extension policy

Prefer small, reviewable dependencies and vendor-neutral interfaces.

Before adding code, data, a model, device SDK, protocol implementation, or
reference archive:

1. Record source, exact version/commit, hash, license, notice obligations, and
   maintainer in `third_party/` or the relevant model/dataset card.
2. Confirm compatibility with Apache-2.0 and whether redistribution is allowed.
3. Keep proprietary or unlicensed material outside Git.
4. Add a contract test and document the supported capability and failure state.
5. Avoid hidden network calls, telemetry, patient-data upload, or automatic
   model download.
6. Pin versions only after device/OS validation; do not upgrade for novelty.

The commit-pinned reference archives in `third_party/reference-repositories/`
are research inputs, not automatically linked or redistributed dependencies.
