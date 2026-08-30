# Publish workflow — review follow-ups

Deferred findings from the round-1 agent review of PR #61 (`release/v0.7.1`). These are work-in-progress notes, deliberately not release-facing.

## The build backend is unpinned, so reproducibility is only conditionally guaranteed

- **Raised by:** Greptile, P2, on [PR #61](https://github.com/Pipelex/kajson/pull/61), thread anchored at `.github/workflows/publish-pypi.yml:163-170` — *"Reruns replace published artifacts … Without a reproducible-build guarantee, this can give the same version different hashes across PyPI and GitHub."*
- **Verdict at the time:** the substantive half (a *different commit* replacing a tagged release's assets) was a duplicate of the Codex/cubic P1 and was fixed by gating `skip-existing` on `github.run_attempt > 1`. The reproducibility half was rejected as a false positive: kajson builds with hatchling, whose `reproducible` build option defaults to `true` and uses a fixed default timestamp when `SOURCE_DATE_EPOCH` is unset, so rebuilding the same commit yields byte-identical artifacts.
- **The residual:** that rejection rests on hatchling's behaviour, and `pyproject.toml` `[build-system] requires = ["hatchling"]` names no version. A hatchling release landing between run attempt 1 and a later recovery re-run could change the bytes, and the GitHub Release assets would then diverge from PyPI's immutable originals for the same version.
- **Why deferred:** the window is narrow (a recovery re-run of an already-published version, spanning a hatchling release), nothing installs from the GitHub assets, and pinning a build backend is a separate call about how this repo wants its builds bounded — not a fix to make inside a release PR.
- **Option if picked up:** pin the backend, e.g. `requires = ["hatchling==<version>"]`, or set `SOURCE_DATE_EPOCH` from the commit timestamp in the `build` job. Either makes the guarantee unconditional; neither is required for the fixes that landed in #61.
