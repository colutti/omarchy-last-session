# Session layout implementation plan

Goal: restore the actual open application windows to their monitors, workspaces and geometry, without a fixed application list or browser-profile edits.
Architecture: retain the upstream event-driven snapshot and pairing pipeline; correct scheduling, add a geometry-oriented mode and reconstruct dwindle splits from saved rectangles. Private runtime state and host configuration never enter Git.

## Tasks
- [x] 1. Add scheduler regression for a close overlapping the periodic deadline; wait until the disappearance settle deadline instead of spinning. Run the full unit suite and commit separately for upstream reuse.
- [x] 2. Add configurable geometry-only restoration, disable browser preference modification in that mode, capture a previous atomic snapshot, and remove the initial autosave gap. Test old defaults and new behavior.
- [x] 3. Infer dwindle splits from nonoverlapping saved rectangles; reconstruct through documented preselect, float and splitratio dispatchers; validate with isolated real compositor windows. Keep tiled windows tiled. Restore geometry after monitor placement.
- [x] 4. Document mode and limits, review all changes, push branch to fork. Install from the reviewed branch with a private rollback copy, remove only equivalent application autostarts, initialize the snapshot and verify monitoring and idle cost. Do not reboot the user's desktop.

## Review focus
Repeated same-class windows; monitor absent or delayed; fullscreen/groups obscuring tile geometry; shutdown snapshot erosion; no busy waits; no browser preference writes in geometry-only mode.

## Decisions
The user authorized implementation and installation. Native execution is used. This dedicated clean clone isolates the work from unrelated work. Public Git contains generic code and fictional tests only. Exact restoration is conditional on monitor geometry and application constraints remaining compatible; unsupported layouts must log a clear fallback.

Validation checkpoint: 533 unit tests pass; real Hyprland 0.56.2 isolated reboot restores unequal nested tiles and floating geometry exactly across two differently scaled monitors. Python strict type checking passes. Fullscreen and grouped multi-tile workspaces use a logged fallback because their visible rectangles do not encode the hidden split tree.

Independent review found a second scheduler boundary case when a vanished window returns to the original layout after the periodic deadline. Added a failing regression and fixed the settle deadline consistently. All 533 unit tests pass. Grouped/fullscreen multi-tile geometry remains a documented limitation; no compositor patches are used.

Integration adjustment: load only Omarchy helpers, appearance and window rules in isolated compositors; full desktop autostart contaminated test windows and host activation variables. Restored the host activation environment and confirmed it remains unchanged after the corrected three-test live suite. All three live tests pass, including monitor removal. Added explicit trusted per-class launchers for sandboxed helpers such as Steam; private local mapping uses steam without replaying sandbox arguments.

Final checkpoint: installation enabled with private backups, equivalent application autostarts and placement rules removed, and three power-menu actions wired to snapshot protection. Six current application windows captured, including Steam through an explicit trusted launcher. Idle sample over 60 seconds: monitor process about 20 MiB RSS, CPU ticks unchanged at the measurement resolution, 24 KiB disk writes; child process CPU is not included. Runtime data remains outside Git. Both strict type checkers, lint, formatting, manifest validation and 533 unit tests pass. No host reboot performed.
