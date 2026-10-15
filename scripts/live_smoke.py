"""Opt-in SEC smoke check. Set SEC_CONTACT in your process environment first.

Never run this in ordinary CI. This checks a real historical filing without printing
or persisting your identification header. Public response cache is ignored by Git.
"""

import os

from filing_lens.filings import parse_sections, retrieve
from filing_lens.financials import compare, select_annual
from filing_lens.sec import SecClient, recent_filings


def main():
    contact = os.environ.get("SEC_CONTACT")
    if not contact:
        raise SystemExit("Set SEC_CONTACT to your real name and email, then run again.")
    client = SecClient(contact)
    cik = client.resolve("AAPL")
    filings = recent_filings(client.json(f"https://data.sec.gov/submissions/CIK{cik}.json"))
    selected = next((f for f in filings if f.report_date == "2024-09-28"), None)
    if selected is None:
        raise SystemExit("Apple FY2024 no longer appears in recent submissions; inspect manually.")
    document = client.fetch(selected.url)
    sections = parse_sections(document.content)
    evidence = retrieve(sections, "What outsourcing partners does the company depend on?")
    if not evidence or evidence[0].item != "1A":
        raise SystemExit("Unexpected retrieval result; inspect the original filing.")
    facts = client.json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
    expected = {
        "Revenue": (383285000000, 391035000000),
        "Net income": (96995000000, 93736000000),
        "Operating income": (114301000000, 123216000000),
    }
    for metric, amounts in expected.items():
        observations = select_annual(facts, metric, selected.accession)
        if tuple(f.value for f in observations[-2:]) != amounts:
            raise SystemExit(f"Unexpected {metric} observations; inspect the source.")
        result = compare(*observations[-2:])
        print(
            f"PASS {metric}: {result.prior.end} -> {result.current.end}; "
            f"change USD {result.change}; percentage {result.percent:.4f}%"
        )
    print(
        f"PASS live SEC: {selected.accession}; {len(sections)} detected sections; "
        f"top evidence Item {evidence[0].item}"
    )


if __name__ == "__main__":
    main()
