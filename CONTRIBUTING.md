# Contributing

Small, understandable changes are welcome. This project prioritizes provenance and financial
correctness over feature count. Explain the user problem before proposing a solution.

1. Install the project with development dependencies as shown in README.
2. Create a short-lived branch: `git switch -c fix/describe-the-change`.
3. Add a failing test for the behavior you intend to change.
4. Make the smallest clear fix. Keep numerical logic out of model prompts.
5. Run `python -m pytest`, `python -m ruff check .`, `python -m ruff format --check .`
   and `python scripts/evaluate.py`.
6. For UI changes, run Streamlit, check a narrow window, and attach a demo screenshot with
   no personal contact information. For parsing changes, test realistic headings and TOCs.
7. Submit a PR explaining behavior, evidence and limitations. Do not claim accuracy from
   a handful of handpicked examples.

Unit tests are offline. Live SEC checks are opt-in, require a real contact, and must not run
in ordinary CI. Do not upload full filings, personal research questions, `.env` or cache files.
Never remove an inconvenient test to make a change pass. Keep dependencies small and explain
why a new one is needed. Respect the licenses of dependencies, source data and model weights.

Before adding metrics, define the accounting concept, units, period type, comparability rules
and failure behavior. Adding a tag to a list does not prove two concepts are interchangeable.
