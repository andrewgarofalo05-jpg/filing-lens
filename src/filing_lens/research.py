"""JSON interface for an AI agent. No model, web UI or paid service is required."""

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from filing_lens.demo import load_demo
from filing_lens.filings import parse_sections, retrieve
from filing_lens.financials import METRICS, compare, select_annual
from filing_lens.sec import SecClient, SecError, recent_filings


def research(bundle: dict, question: str, metric: str | None, end: str | None) -> dict:
    filing = bundle["filing"]
    evidence = retrieve(bundle["sections"], question) if question else []
    result = {
        "schema_version": 1,
        "demo": bundle["demo"],
        "filing": asdict(filing),
        "filing_fetched_at": bundle["filing_fetched_at"],
        "facts_fetched_at": bundle["facts_fetched_at"],
        "question": question,
        "evidence": [asdict(p) for p in evidence],
        "comparison": None,
        "warnings": [
            "Research and education only; not investment advice.",
            "Item labels are heuristic. Check passages in the original filing.",
        ],
    }
    if bundle["demo"]:
        result["warnings"].append("Curated historical demo; not a full filing or live data.")
    if question and not evidence:
        result["warnings"].append("No supporting passage retrieved; do not infer an answer.")
    if metric:
        facts = select_annual(bundle["facts"], metric, filing.accession)
        if end:
            facts = [fact for fact in facts if fact.end <= end]
            if not facts or facts[-1].end != end:
                raise ValueError("Requested period end is unavailable for this metric and filing.")
        if len(facts) < 2:
            result["warnings"].append(
                "Fewer than two compatible annual facts; comparison unavailable."
            )
        else:
            result["comparison"] = asdict(compare(*facts[-2:]))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true", help="Offline Apple FY2024 sample")
    source.add_argument("--company", help="Ticker or numeric CIK; requires SEC_CONTACT")
    parser.add_argument("--list-filings", action="store_true")
    parser.add_argument("--accession", help="Explicit original 10-K accession from --list-filings")
    parser.add_argument("--question", default="", help="At most 1,000 characters")
    parser.add_argument("--metric", choices=list(METRICS))
    parser.add_argument(
        "--end", help="Current annual period end YYYY-MM-DD; defaults to latest pair"
    )
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache/sec"))
    args = parser.parse_args(argv)
    try:
        if len(args.question) > 1000:
            raise ValueError("Keep questions under 1,000 characters.")
        if args.end:
            from datetime import date

            date.fromisoformat(args.end)
        if args.demo:
            if args.accession or args.list_filings:
                raise ValueError("The demo uses one fixed filing; omit live filing options.")
            bundle = load_demo()
        else:
            contact = os.environ.get("SEC_CONTACT", "")
            if not contact:
                raise ValueError(
                    "Set SEC_CONTACT to your real name and email for SEC identification."
                )
            if not args.list_filings and not args.accession:
                raise ValueError("Use --list-filings first, then choose an explicit --accession.")
            client = SecClient(contact, args.cache_dir)
            cik = client.resolve(args.company)
            filings = recent_filings(client.json(f"https://data.sec.gov/submissions/CIK{cik}.json"))
            if args.list_filings:
                print(json.dumps({"schema_version": 1, "filings": [asdict(f) for f in filings]}))
                return 0
            chosen = next((f for f in filings if f.accession == args.accession), None)
            if chosen is None:
                raise ValueError(
                    "Accession is not a supported recent original 10-K for this company."
                )
            document = client.fetch(chosen.url)
            facts_response = client.fetch(
                f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            )
            facts = json.loads(facts_response.content)
            if not isinstance(facts, dict) or "facts" not in facts:
                raise ValueError("Unexpected SEC Company Facts response.")
            bundle = dict(
                filing=chosen,
                sections=parse_sections(document.content),
                facts=facts,
                filing_fetched_at=document.fetched_at,
                facts_fetched_at=facts_response.fetched_at,
                demo=False,
            )
        print(
            json.dumps(
                research(bundle, args.question, args.metric, args.end), indent=2, default=str
            )
        )
        return 0
    except (ValueError, SecError, OSError) as exc:
        print(json.dumps({"schema_version": 1, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
