# Verification record — October 15, 2026

## Completed locally

| Check | Result |
| --- | --- |
| Python/OS | CPython 3.11.16 on Windows |
| pytest | 43 passing offline tests; real requests disabled in the suite |
| Ruff lint and formatting | Passed |
| Small evaluation | 11/11: eight synthetic retrieval/abstention cases, three demo calculations |
| Packaging | Source distribution and wheel built successfully; demo data packaged |
| Browser | Headless Microsoft Edge; evidence search, comparison, source tabs; no page errors |
| Layout | Desktop 1440px and narrow 390px screenshots inspected |
| Runtime dependency audit | pip-audit reported no known vulnerabilities for exported locked runtime dependencies |
| Live SEC | Apple FY2024 submissions, HTML parsing, Risk Factors retrieval and annual financial facts checked |
| Source review | Separate read-only review of transport, financial logic, AI boundaries and UI state; no must-fix findings |
| AI skill | Skill validator passed; JSON helper tested for cited evidence, exact arithmetic, missing contact and abstention |

Live test source: accession `0000320193-24-000123`, filed 2024-11-01. The parser detected
23 item sections in the actual downloaded HTML. The outsourcing query's top result was Item 1A.
Annual revenue observations were $394.328bn (FY2022), $383.285bn (FY2023), and $391.035bn
(FY2024). FY2023→FY2024 revenue change was $7.750bn and 2.021994…%, before display rounding.
The selected periods have 53 and 52 weeks; the app displays a length warning.
The live smoke script also matched FY2023/FY2024 net income ($96.995bn/$93.736bn) and
operating income ($114.301bn/$123.216bn), with changes of -$3.259bn and +$8.915bn respectively.

The user's actual contact header was used only for live SEC access, not saved in project files,
cached response metadata or screenshots. Full live downloads are excluded from the release.

## Not verified / not claimed

- Ollama was not available at localhost:11434. Real local-model inference and output quality
  were **not** tested. The adapter, rejection cases and prompt/tool boundary were tested with
  controlled responses. Do not describe this as a measured AI accuracy result.
- GitHub Actions has been prepared but has not run on GitHub. Linux/Python 3.12 matrix results
  are not claimed from a local Windows/Python 3.11 check.
- One live company/filing smoke check is not broad SEC compatibility coverage.
- No load test, hosted multi-user security assessment, formal accessibility audit or independent
  accounting assurance was performed.
- A dependency audit is a point-in-time known-advisory check, not a guarantee of safety.

## Reproduce

Follow README setup, then run tests, lint, format check and `scripts/evaluate.py`.
For live access, set a process-local `SEC_CONTACT` to your real name/email and run
`python scripts/live_smoke.py`. It never prints the contact. Do not store the value in Git.
For optional AI, install a local model, run the app, generate a qualitative draft and compare
every claim to the displayed evidence. Record the model/version and failures honestly.
