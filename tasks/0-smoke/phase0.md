# Phase 0: smoke

## Goal

Verify that `scripts/run_phases.py` can launch a Codex phase and observe the phase status update.

## Work

Do not change application, harness, skill, or documentation files.

Only update `tasks/0-smoke/index.json` so phase `0` has:

```json
"status": "completed"
```

## Acceptance Criteria

- `tasks/0-smoke/index.json` contains phase `0` with `"status": "completed"`.
- No files are changed except `tasks/0-smoke/index.json` and runner-generated output/timestamp files.
