# Manual Merge Guide for Alpha Omega Arcade

The current container cannot push to GitHub because outbound access to GitHub is blocked by the environment proxy (`CONNECT tunnel failed, response 403`). This file provides a reproducible, normal Git merge path for `https://github.com/Goated233/alpha-omega` without claiming that anything was pushed or merged from this environment.

## Current local commit

```bash
git log --oneline -1
# bb8a44b Initial platform: Alpha Omega Arcade - core services, games, UI, infra, DB, and tests
```

## Option A: Push this branch normally from a machine with GitHub access

Run these commands from this repository checkout on a machine that can reach GitHub:

```bash
git remote set-url origin https://github.com/Goated233/alpha-omega.git
git status --short
git branch --show-current
git push -u origin HEAD:alpha-omega-arcade-platform
```

Then merge normally on GitHub:

```bash
# Browser flow:
# 1. Open https://github.com/Goated233/alpha-omega/pulls
# 2. Create a PR from alpha-omega-arcade-platform into the default branch
# 3. Review CI and merge
```

Or merge locally and push the default branch:

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git merge --no-ff alpha-omega-arcade-platform -m "Merge Alpha Omega Arcade platform"
git push origin main
```

If the repository default branch is `master` instead of `main`, replace `main` with `master`.

## Option B: Export and apply a patch

Generate a patch from the local implementation commit range:

```bash
python scripts/export_merge_artifacts.py --base eedc358 --head HEAD --out dist
```

This writes:

- `dist/alpha_omega_platform.patch` — a Git patch that can be applied to the target repo.
- `dist/alpha_omega_full_file_contents.md` — full contents for every changed file.
- `dist/alpha_omega_changed_files.txt` — explicit changed-file manifest.

Apply the patch in a clean clone:

```bash
git clone https://github.com/Goated233/alpha-omega.git
cd alpha-omega
git checkout -b alpha-omega-arcade-platform
git apply /path/to/dist/alpha_omega_platform.patch
git status --short
python -m compileall app core database engines games ui admin infra workers utils tests
python -m ruff check .
pytest -q
git add .
git commit -m "Initial platform: Alpha Omega Arcade - core services, games, UI, infra, DB, and tests"
git push -u origin alpha-omega-arcade-platform
```

## Changed-file manifest

To show every changed file explicitly:

```bash
git diff --name-only --diff-filter=ACMR eedc358..HEAD
```

To show the complete patch directly in the terminal:

```bash
git diff --binary eedc358..HEAD
```

To show full contents of every changed file directly in the terminal:

```bash
python scripts/export_merge_artifacts.py --base eedc358 --head HEAD --stdout-contents
```

## Verification commands

Run these before pushing from a normal networked machine:

```bash
python -m compileall app core database engines games ui admin infra workers utils tests
python -m ruff check .
pytest -q
git diff --check eedc358..HEAD
```
