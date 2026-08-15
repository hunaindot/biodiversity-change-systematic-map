# retired-helpers

Snapshots of `data_helpers` code that was removed from the live modules as dead
(zero references outside its own definition, `__all__` entry, and — where noted
— its own dedicated unit test). Each dated subfolder is one cleanup pass; read
its own notes before assuming a module or symbol is gone for good.

## Why this folder was recreated on 2026-08-15

An earlier version of this folder existed (per `CLAUDE.md` and
`.claude/memories/decisions-log.md`, holding the 2026-08-01 dead-symbol
snapshot plus retired F4 predecessor notebooks, the archived climate
notebooks, `03_unchecked_realm_composition.ipynb` + `threat.py`, and more) but
was **never actually committed to git**, despite `CLAUDE.md` explicitly
claiming `notebooks/results/archive/` was "git-tracked, not gitignored."
Checking `git log --all` for this path shows only 5 files were ever tracked
under `notebooks/results/archive/`, all under `outputs/02_income_composition/`
— `retired-helpers/` itself has zero history. The directory existed only as
loose, untracked files on disk, and vanished from disk sometime during the
2026-08-15 session that discovered this (most likely swept up in unrelated
manual cleanup elsewhere, since an untracked directory shows as a single `??`
line in `git status` — easy to delete without seeing what's inside).

**Everything that folder held before 2026-08-15 is unrecoverable** unless it
exists in a non-git backup (e.g. Time Machine) outside this repo's own
history. This subfolder (`2026-08-15-orphan-code-cleanup/`) is the first
addition since the loss, and — unlike its predecessor — was `git add`ed
immediately so the same failure mode can't silently repeat. **Treat every
"archived here, recoverable via this folder" claim elsewhere in `CLAUDE.md` or
the decisions log as describing a state that no longer exists on disk**, until
each is individually re-verified and, if still wanted, re-created and
committed.

## Subfolders

- `2026-08-15-orphan-code-cleanup/` — `removed_symbols.py`: 15 symbols across 6
  `data_helpers` modules (a legacy raw-CSV loading sub-pipeline in
  `analysis/taxa/skew.py`, a dead result-store method, two superseded plotting
  functions, one unused clipart helper, one unused prep helper), removed after
  a repo-wide orphan-code audit. See that file's header for full detail and the
  2026-08-15 decisions-log entry for the request/rationale.
