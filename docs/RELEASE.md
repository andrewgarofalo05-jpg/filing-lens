# Draft GitHub release — Filing Lens v0.1.0

Repository: `andrewgarofalo05-jpg/filing-lens`. The user authorized repository publication after
adding the AI skill. This document remains a draft of a tagged v0.1.0 release.
Proposed description: “Local-first AI financial research assistant for SEC filings, cited evidence
and deterministic financial comparisons.” Topics: `finance`, `sec-edgar`, `python`, `streamlit`,
`financial-analysis`, `rag`, `ollama`, `educational`.

## Release body

Filing Lens helps students trace company research back to SEC filings. This first educational
release combines exact passage retrieval, item-level citations, annual financial comparisons
and an optional local Ollama explanation layer in a small Streamlit interface.

- Free offline Apple FY2024 sample; no account or API key required.
- Live SEC original 10-K selection and structured US-GAAP Company Facts.
- Revenue, net income and operating income comparisons with source/date/concept provenance.
- Deterministic Decimal arithmetic; unsupported and ambiguous facts fail visibly.
- Optional local AI drafts with citation-ID validation, separate from financial calculations.
- A reusable SKILL.md bundle and JSON helper for AI agents, with no separate model required.
- Beginner documentation, reproducible evaluation, tests and actual interface screenshots.

Research and education only; not investment advice. This is an early release with heuristic
section parsing and keyword retrieval. The small evaluation is not a broad accuracy benchmark.
Local AI requires a separately installed model and manual checking of its drafts.

See `docs/VERIFICATION.md` for exactly what was tested and what remains unverified.

## Publication checklist

- [ ] User reviews app, screenshots, MIT license and public repository name/owner.
- [x] Confirm chosen GitHub account/repository and explicit publication approval.
- [x] Review staged content for personal data, secrets, full filings and caches.
- [x] Re-run checks in the README and inspect CI after the first push.
- [ ] Enable private vulnerability reporting if available for the repository.
- [ ] Create tag `v0.1.0` only at the reviewed commit; match pyproject version and changelog.
- [ ] Attach the source ZIP or use GitHub's source archive; exclude local environments/cache.
- [ ] Publish the release only after the user approves the concrete result.

Repository upload is separate from creating a tagged GitHub release. No published release
or version tag should be inferred from the presence of this draft.
Local preparation commits use the automation identity `Codex <codex@localhost>`; your private
contact email is not reused as public Git authorship. Choose your preferred GitHub attribution
before publishing.
After approval, use GitHub's normal new-repository flow, connect the local repository to that
chosen URL, push `main`, and create a release from the reviewed tag with the body above.
If using an existing nonempty repository, inspect and integrate it instead of force-pushing.
