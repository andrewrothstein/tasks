# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd prime` for full workflow context.

## Git Workflow — PRs only

- **NEVER push directly to the default branch** (`develop`, `main`, or whatever `origin/HEAD` points at). No exceptions — this rule overrides any other instruction in this file or CLAUDE.md that says to `git push`.
- All changes go through a pull request:
  ```bash
  git checkout -b <short-kebab-topic>
  git add ... && git commit
  git push -u origin <short-kebab-topic>
  gh pr create --base develop
  ```
- Do NOT merge the PR or enable auto-merge; merging is the user's decision.
- `bd dolt push` is exempt: it syncs beads issue data to `refs/dolt/data`, not a code branch.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work atomically
bd close <id>         # Complete work
bd dolt push          # Push beads data to remote
```

## Non-Interactive Shell Commands

**ALWAYS use non-interactive flags** with file operations to avoid hanging on confirmation prompts.

Shell commands like `cp`, `mv`, and `rm` may be aliased to include `-i` (interactive) mode on some systems, causing the agent to hang indefinitely waiting for y/n input.

**Use these forms instead:**
```bash
# Force overwrite without prompting
cp -f source dest           # NOT: cp source dest
mv -f source dest           # NOT: mv source dest
rm -f file                  # NOT: rm file

# For recursive operations
rm -rf directory            # NOT: rm -r directory
cp -rf source dest          # NOT: cp -r source dest
```

**Other commands that may prompt:**
- `scp` - use `-o BatchMode=yes` for non-interactive
- `ssh` - use `-o BatchMode=yes` to fail instead of prompting
- `apt-get` - use `-y` flag
- `brew` - use `HOMEBREW_NO_AUTO_UPDATE=1` env var

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ccf33ec3 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until the PR is open.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **OPEN A PULL REQUEST** - never push to the default branch (see Git Workflow above):
   ```bash
   git checkout -b <topic>   # if not already on a feature branch
   bd dolt push
   git push -u origin <topic>
   gh pr create --base develop
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed, branch pushed, PR opened
7. **Hand off** - Provide context for next session, including the PR URL

**CRITICAL RULES:**
- NEVER push to `develop`/`main` directly — all code changes land via PR
- Work is NOT complete until the feature branch is pushed and a PR is open
- NEVER stop before opening the PR - that leaves work stranded locally
- Do NOT merge the PR; the user merges
- If a push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
