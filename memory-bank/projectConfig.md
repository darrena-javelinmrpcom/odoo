# Project Configuration

## Banyan Memory Bank

This section is auto-managed by `/bmb:init`. Do not edit manually.

- **Banyan Version**: 2.2.1
- **Initialized**: 2026-10-20
- **Last Updated**: 2026-10-20

## Git & Branching (v2)

```yaml
metadata_branch: banyan
protected_branches: [banyan]
pr_target: banyan
sync_automation: none
archive_strategy: push-and-pr
worktree_root: ~/banyan-wt/odoo/
```

## Agent Backends

```yaml
backends:
  plan:                  anthropic
  tdd:                   anthropic
  code-review:           anthropic
  creative-architecture: anthropic
  creative-uiux:         anthropic
  creative-algorithm:    anthropic
  creative-user-journey: anthropic
  creative-critique:     codex
  auto-final-review:     anthropic
  availability:          auto
```

## Team

team:
  # <git-email>: <friendly first name> — self-populating; see
  # context/branch-routing.md § Team Roster. Do not collect the full team here.
  darrena@javelin-mrp.com: darrena-javelinmrpcom

## UAT

Project-wide defaults for `/bmb:uat`. Edit freely — these are read at the start of every UAT run. Infra/secrets live in `memory-bank/uat-config.md`.

- **default_sections**: happy,mobile         # happy | mobile | negatives | errors | all
- **default_skip_ux_check**: false
- **default_environment**: dev                # environments[*].name in uat-config.md
- **artifact_git_policy**: ignore             # ignore | commit
- **uat_required_for_archive**: false
