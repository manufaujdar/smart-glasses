# Device validation plan

## Metrics

| Area | Metric | Prototype target |
|---|---|---|
| Connection | successful connect within 10 s | >= 95% over 50 cycles |
| Recovery | reconnect after transient loss | <= 15 s, no duplicate command |
| Command | acknowledged photo command | >= 99% over 100 attempts |
| Media | transferred file checksum match | 100% |
| Audio | intelligible medical phrases in representative noise | establish baseline by room type |
| Battery | mixed-use duration | >= 4 h or documented hot-swap path |
| Thermal | user-contact discomfort | none in two-hour session |
| Privacy | capture indicator and stop | 100% observable and functional |
| Audit | commanded/result events paired | 100% |

## Test environments

- quiet office
- simulated ward
- simulated OR noise and lighting
- mask, cap, shield and prescription glasses combinations
- congested hospital Wi-Fi/BLE environment

## Safety stop rules

Stop testing if the device becomes uncomfortably hot, captures while indicated as stopped, repeatedly associates media with the wrong session, silently loses commands, exposes an open Wi-Fi transfer service, or cannot be reliably sanitized.

