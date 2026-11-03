---
name: Git Worktrees on Windows (learned)
globs: []
paths: []
topics: ["git", "worktree", "windows", "onedrive", "subagents", "isolation"]
priority: low
auto_generated: true
derived_from: [fitness-no-cross-module-imports]
evidence_count: 1
last_validated: 2026-11-03
---

# Git Worktrees on Windows

- This repo needs `git config core.longpaths true` before any worktree is created; Odoo test-fixture paths exceed MAX_PATH and a failed checkout leaves orphan branches.
- For agent isolation, prefer detached sparse worktrees (only the needed directories) under `worktree_root`, outside OneDrive. A full worktree is ~43k files and would sync to OneDrive.
- Verify every precondition a scenario relies on (addons, files) exists at HEAD before fanning out agents.
