# Source and calculation methodology

## Evidence chain

1. Resolve a ticker using SEC company_tickers.json, or accept a validated numeric CIK.
2. Read the company's recent submissions and show up to ten original 10-Ks.
3. Download the selected primary HTML document and the company's Company Facts JSON.
4. Preserve accession, report date, filing date, canonical URL and separate fetch timestamps.
5. Parse item headings, retain the longest duplicate section (usually excluding a short TOC),
   and split text into paragraphs/chunks. Inline tags are flattened; no page number is invented.
6. Rank chunks by query-token overlap with inverse document frequency weighting. Require at
   least 25% of significant query terms to overlap. These scores are rankings, not probabilities.
7. Return up to three exact text chunks with item/title and a SHA-256-derived passage ID.

The parser assumes ordinary English 10-K item headings. Cross-references, unusually formatted
headings, nested tables, hidden content and duplicated items can confuse it. No-heading documents
are explicitly marked Unclassified. Always use the original link to check the surrounding text.
No claim is made that the selected passage fully answers every question.

## Annual fact selection

Only `us-gaap` facts, `USD` units, original `10-K` rows and the **selected accession** qualify.
A fact must have a start/end duration of 350–380 days. This accepts ordinary fiscal years and
52/53-week calendars while rejecting quarterly/YTD observations and most transition periods.
The SEC `fy` field describes the filing fiscal year; it is not the comparison period's year.

Revenue concepts are tried in explicit order: RevenueFromContractWithCustomerExcludingAssessedTax,
Revenues, SalesRevenueNet. Use the first with eligible facts; never merge years across aliases.
Net income uses NetIncomeLoss; operating income uses OperatingIncomeLoss. No custom-tag guessing.
Duplicate equal facts collapse. Conflicting values or starts for the same end date raise an error.
The app makes a conservative tradeoff: missing output is preferable to a silently wrong mapping.

Comparisons require the same metric, tag, unit and accession, with the current period starting
the day after the previous period ends. Differing year lengths produce a warning.

```text
absolute change = current − prior
percentage change = (current − prior) / prior × 100, only when prior > 0
```

Use Decimal arithmetic. JSON exports retain full decimal strings; the UI rounds only presentation.
Zero or negative baselines show the dollar change but omit ordinary percentage growth.
There is no annualization or adjustment for inflation, acquisitions, divestitures or extra weeks.
Figures reflect the comparative presentation in the selected filing, including any restatement
already reflected there. Later amendments or restatements are not automatically reconciled.

## SEC access policy

The app identifies itself with the user's real name/email; the SEC has no API-key requirement
for these endpoints. It spaces request starts by at least 0.6 seconds in one process, caches
public responses for 24 hours, and retries timeouts/selected server errors at most twice.
403/429 responses stop requests for at least ten minutes or longer if Retry-After specifies it.
Redirects, proxy rotation and identity spoofing are not used to evade blocks.

Official references checked October 15, 2026:

- [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC developer resources and fair access](https://www.sec.gov/about/developer-resources)
- [SEC accessing EDGAR data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- [Apple 2024 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm)

Policies and endpoints can change. Recheck these references before expanding or hosting the app.
