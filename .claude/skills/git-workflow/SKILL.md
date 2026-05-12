---
name: git-workflow
description: >
  Git workflow expert for development teams. Use when creating branches, making commits,
  rebasing, squashing, merging, resolving conflicts, recovering from mistakes, or
  reviewing Git history. Covers: rebase + squash workflow (rebase local, squash al merge,
  merge --no-ff via PR), conventional commits, branch naming conventions, rescue commands
  (undo merge, recover deleted branch, reset mistakes, cherry-pick), conflict resolution,
  and safe force-push patterns. Critical: never force push to main or shared branches.
  Activate whenever the user mentions git, branches, commits, merge, rebase, PR, pull
  request, push, conflict, undo, reset, reflog, cherry-pick, or version control.
---

# Git Workflow

## SAFETY RULES (CRITICAL — Read First)

Three rules that are never negotiable. Breaking them corrupts shared history.

### Rule 1: NEVER force push to main or shared branches

```bash
# ❌ NEVER — destroys shared history
git push --force origin main
git push --force origin develop

# ✅ Only force push YOUR feature branch (you're the only one on it)
git push --force-with-lease origin feature/my-task
```

`--force-with-lease` is safer than `--force`: it fails if someone else pushed to the
branch since your last fetch. Always use `--force-with-lease` instead of `--force`.

### Rule 2: NEVER rebase commits that exist on a shared branch

Rebase rewrites commit hashes. If those commits already exist on `main` or a branch
others are working on, rebase creates duplicates and divergent history.

```bash
# ✅ Safe: rebase YOUR local feature branch onto main
git checkout feature/billing
git rebase main

# ❌ DANGEROUS: rebase main onto anything
git checkout main
git rebase feature/billing
```

### Rule 3: NEVER commit secrets, credentials, or .env files

```bash
# Verify before every commit
git diff --cached --name-only | grep -E '\.env|secret|credential|password|key'

# If already committed, remove from history (destructive — coordinate with team)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' HEAD
```

---

## Branch Naming Convention

Format: `type/short-description`

| Prefix | Use |
|--------|-----|
| `feature/` | New functionality |
| `fix/` | Bug fix |
| `hotfix/` | Urgent production fix (branches from main) |
| `refactor/` | Code restructuring without behavior change |
| `chore/` | Dependencies, config, tooling |
| `docs/` | Documentation only |
| `test/` | Adding or fixing tests |

```bash
# ✅ Good
feature/user-billing
fix/login-redirect-loop
hotfix/payment-timeout
refactor/extract-territory-resolver

# ❌ Bad
billing                    # No prefix — unclear intent
feature/fix-stuff          # Vague
Feature/UserBilling        # Don't capitalize
feature/implement-the-new-billing-module-for-saas  # Too long
```

Keep branch names under 50 characters. Use kebab-case. No spaces, no underscores.

---

## Conventional Commits

Format: `type(scope): description`

Scope is optional. Description is lowercase, imperative, no period.

| Type | When |
|------|------|
| `feat` | New feature visible to user |
| `fix` | Bug fix |
| `refactor` | Code change that doesn't fix a bug or add a feature |
| `chore` | Build, deps, config — no production code change |
| `docs` | Documentation only |
| `test` | Adding or correcting tests |
| `style` | Formatting, whitespace — no logic change |
| `perf` | Performance improvement |
| `ci` | CI/CD config changes |

```bash
# ✅ Good
feat(billing): add stripe webhook handler
fix(auth): prevent redirect loop on expired token
refactor(imports): extract phone validation to service
chore: upgrade laravel to 12.1
test(users): add cerberus permission tests
docs: update deployment checklist

# ❌ Bad
Fixed bug                          # No type, past tense, vague
feat: Added new feature            # Past tense, vague
FEAT(BILLING): ADD PAYMENTS        # No caps
feat(billing): add stripe webhook handler.  # No period at end
```

### Breaking changes

Add `!` after type or `BREAKING CHANGE:` in body:

```bash
feat(api)!: change user endpoint response format

# Or in body:
feat(api): change user endpoint response format

BREAKING CHANGE: user.name split into user.firstName and user.lastName
```

---

## Workflow: Rebase + Squash (Default)

This is the active workflow. Clean linear history, atomic commits in main.

### The cycle

```
1. Create feature branch from main
2. Work: commit freely (small, frequent commits)
3. Stay updated: rebase onto main regularly
4. Finish: squash into one semantic commit
5. Push and create PR
6. Merge via PR (merge --no-ff)
7. Delete feature branch
```

### Step 1 — Create branch

```bash
git checkout main
git pull origin main
git checkout -b feature/billing-webhooks
```

### Step 2 — Work and commit freely

During development, commit often. These will be squashed later.

```bash
git add .
git commit -m "wip: stripe webhook scaffold"
git commit -m "wip: add signature verification"
git commit -m "fix: handle duplicate events"
git commit -m "test: webhook endpoint tests"
```

### Step 3 — Stay updated with main

Do this daily, or before pushing. Rebase your branch onto latest main:

```bash
git fetch origin
git rebase origin/main
```

If conflicts arise during rebase:

```bash
# 1. Fix conflicts in your editor
# 2. Stage resolved files
git add path/to/resolved-file.php

# 3. Continue rebase
git rebase --continue

# If it's a mess and you want to abort:
git rebase --abort
```

### Step 4 — Squash before merging

When the feature is complete, squash all commits into one:

```bash
# Count your commits since branching from main
git log --oneline main..HEAD
# Example output: 4 commits

# Interactive rebase to squash
git rebase -i HEAD~4
```

In the editor, change `pick` to `s` (squash) for all except the first:

```
pick abc1234 wip: stripe webhook scaffold
s def5678 wip: add signature verification
s ghi9012 fix: handle duplicate events
s jkl3456 test: webhook endpoint tests
```

Save, then write a clean semantic message:

```
feat(billing): add stripe webhook handler

- Verify webhook signatures with Stripe SDK
- Handle invoice.paid and invoice.payment_failed events
- Idempotent: skip duplicate event IDs
- Includes feature tests for all event types
```

### Step 5 — Push

```bash
# First push
git push origin feature/billing-webhooks

# If you already pushed before squashing (force needed)
git push --force-with-lease origin feature/billing-webhooks
```

### Step 6 — Merge via PR

Create Pull Request in GitHub/GitLab. After approval:

The PR merge button should use **"Create a merge commit"** (equivalent to `--no-ff`).
This preserves the branch topology in history — you can see where features were integrated.

```bash
# What the PR does behind the scenes:
git checkout main
git merge --no-ff feature/billing-webhooks
```

### Step 7 — Clean up

```bash
git checkout main
git pull origin main
git branch -d feature/billing-webhooks           # Delete local
git push origin --delete feature/billing-webhooks  # Delete remote
```

---

## Conflict Resolution

### During rebase

```bash
# See which files conflict
git status

# After resolving in editor:
git add path/to/file.php
git rebase --continue

# Skip a commit entirely if it's no longer relevant:
git rebase --skip

# Abort if things go sideways:
git rebase --abort
```

### Prevention

```bash
# Before starting work, always:
git fetch origin
git rebase origin/main

# Keep feature branches short-lived (< 1 week ideally)
# Small PRs = fewer conflicts
```

### Complex conflicts (ours vs theirs during rebase)

During rebase, the terminology is inverted from merge:

- `--ours` = the branch you're rebasing ONTO (main)
- `--theirs` = YOUR changes (the feature branch)

```bash
# Accept main's version of a file:
git checkout --ours path/to/file.php
git add path/to/file.php

# Keep your version:
git checkout --theirs path/to/file.php
git add path/to/file.php
```

---

## Rescue Commands (CRITICAL)

### Undo last commit (keep changes)

```bash
# Soft reset — uncommit but keep staged
git reset --soft HEAD~1

# Mixed reset — uncommit and unstage (files remain modified)
git reset HEAD~1

# Hard reset — DESTROY changes completely
git reset --hard HEAD~1
```

### Undo a merge that hasn't been pushed

```bash
git reset --hard HEAD~1
# Or if merge was 2+ commits ago, find the pre-merge commit:
git reflog
git reset --hard HEAD@{n}
```

### Undo a merge that WAS pushed to main

**Do not rewrite history.** Use `revert` to create an inverse commit:

```bash
git revert -m 1 <merge-commit-hash>
git push origin main
```

`-m 1` means "keep the main branch side, undo the feature branch side."

### Recover a deleted branch

Branches are just pointers. The commits still exist in reflog:

```bash
# Find the last commit of the deleted branch
git reflog | grep "billing"
# or
git reflog --all | head -30

# Recreate the branch at that commit
git checkout -b feature/billing-webhooks abc1234
```

### Recover from a bad rebase

```bash
# Find pre-rebase state in reflog
git reflog
# Look for "rebase (start)" entry — the commit BEFORE it is your safe point

git reset --hard HEAD@{n}
```

### Undo a git add (unstage files)

```bash
# Unstage specific file
git restore --staged path/to/file.php

# Unstage everything
git restore --staged .
```

### Discard local changes (revert file to last commit)

```bash
# Single file
git restore path/to/file.php

# All tracked files
git restore .
```

### Cherry-pick a specific commit

```bash
# Apply a single commit from another branch
git cherry-pick abc1234

# Cherry-pick without committing (stage only)
git cherry-pick --no-commit abc1234

# Cherry-pick a range
git cherry-pick abc1234..def5678
```

### Find who changed a line (blame)

```bash
git blame path/to/file.php
git blame -L 10,20 path/to/file.php   # Lines 10-20 only
git log -p -S "functionName"           # Find when a string was added/removed
```

### Stash work in progress

```bash
# Save current changes
git stash
git stash push -m "billing form halfway done"

# List stashes
git stash list

# Apply most recent stash (keep in stash list)
git stash apply

# Apply and remove from stash list
git stash pop

# Apply specific stash
git stash apply stash@{2}

# Drop a stash
git stash drop stash@{0}
```

---

## Useful Inspection Commands

```bash
# Compact log with branch graph
git log --oneline --graph --all -20

# Commits on your branch not yet in main
git log --oneline main..HEAD

# What changed in a commit
git show abc1234

# Diff between branches
git diff main..feature/billing

# Diff only file names
git diff --name-only main..HEAD

# Search commit messages
git log --grep="billing" --oneline

# Find commits by author
git log --author="name" --oneline --since="1 week ago"
```

---

## Docker Integration

All Git commands in this project run inside the app container or from the host:

```bash
# From host (if git is installed)
git status

# Inside container (if needed)
docker compose exec app git status
```

---

## Checklist for Every PR

1. Branch name follows convention (`type/short-description`)
2. Commits squashed into one semantic commit
3. Commit message follows conventional commits format
4. Rebased onto latest `main` (no merge commits in feature branch)
5. No secrets, `.env`, or credentials in diff
6. No `dd()`, `dump()`, or debug artifacts
7. Tests pass: `docker compose exec app php artisan test`
8. Linter passes: `docker compose exec app vendor/bin/pint --dirty`
