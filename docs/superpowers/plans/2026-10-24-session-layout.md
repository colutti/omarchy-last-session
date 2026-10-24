# Session layout implementation plan

Goal: restore the actual open application windows to their monitors, workspaces and geometry, without a fixed application list or browser-profile edits.
Architecture: retain the upstream event-driven snapshot and pairing pipeline; correct scheduling, add a geometry-oriented mode and reconstruct dwindle splits from saved rectangles. Private runtime state and host configuration never enter Git.

## Tasks
- [ ] 1. Add scheduler regression for a close overlapping the periodic deadline; wait until the disappearance settle deadline instead of spinning. Run the full unit suite and commit separately for upstream reuse.
- [ ] 2. Add configurable geometry-only restoration, disable browser preference modification in that mode, capture a previous atomic snapshot, and remove the initial autosave gap. Test old defaults and new behavior.
- [ ] 3. Infer dwindle splits from nonoverlapping saved rectangles; reconstruct through documented preselect, float and splitratio dispatchers; validate with isolated real compositor windows. Keep tiled windows tiled. Restore geometry after monitor placement.
- [ ] 4. Document mode and limits, review all changes, push branch to fork. Install from the reviewed branch with a private rollback copy, remove only equivalent application autostarts, initialize the snapshot and verify monitoring and idle cost. Do not reboot the user's desktop.

## Review focus
Repeated same-class windows; monitor absent or delayed; fullscreen/groups obscuring tile geometry; shutdown snapshot erosion; no busy waits; no browser preference writes in geometry-only mode.

## Decisions
The user authorized implementation and installation. Native execution is used. This dedicated clean clone isolates the work from the genealogy repository. Public Git contains generic code and fictional tests only. Exact restoration is conditional on monitor geometry and application constraints remaining compatible; unsupported layouts must log a clear fallback.
