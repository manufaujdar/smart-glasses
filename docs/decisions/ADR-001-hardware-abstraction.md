# ADR-001: isolate hardware behind a capability driver

Status: accepted

## Context

The current HeyCyan SDK is proprietary, the available glasses expose only a subset of future platform capabilities, and hardware supply/SDK quality can change quickly.

## Decision

Clinical workflows depend on a vendor-neutral device contract. Each hardware integration lives in a separate adapter. The licensed HeyCyan SDK is a local binary dependency and cannot leak into workflow or server modules.

## Consequences

- We can test with a simulator and replace hardware without rewriting clinical logic.
- Some vendor-specific features will require optional extension capabilities.
- Contract and conformance testing becomes mandatory.

