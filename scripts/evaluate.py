"""A small reproducible regression evaluation; run from the repository root."""

import json
from decimal import Decimal
from pathlib import Path

from filing_lens.demo import load_demo
from filing_lens.filings import parse_sections, retrieve
from filing_lens.financials import compare, select_annual

ROOT = Path(__file__).resolve().parents[1]


def evaluate() -> dict:
    fixture = ROOT / "tests/fixtures"
    sections = parse_sections((fixture / "research.html").read_text(encoding="utf-8"))
    cases = json.loads((fixture / "evaluation.json").read_text(encoding="utf-8"))
    results = []
    for case in cases:
        found = retrieve(sections, case["question"])
        actual = found[0].item if found else None
        exact = all(any(p.text in s.text and p.item == s.item for s in sections) for p in found)
        results.append({**case, "actual": actual, "pass": actual == case["item"] and exact})
    demo = load_demo()
    for metric, change in [
        ("Revenue", "7750000000"),
        ("Net income", "-3259000000"),
        ("Operating income", "8915000000"),
    ]:
        facts = select_annual(demo["facts"], metric, demo["filing"].accession)
        actual = compare(*facts).change
        results.append(
            {
                "metric": metric,
                "expected_change_usd": change,
                "actual_change_usd": str(actual),
                "pass": actual == Decimal(change),
            }
        )
    return {
        "suite": "8 synthetic retrieval cases + 3 manually checked demo calculations",
        "passed": sum(r["pass"] for r in results),
        "total": len(results),
        "limitations": "Not a broad SEC benchmark; no generative-model quality measurement.",
        "cases": results,
    }


if __name__ == "__main__":
    report = evaluate()
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] == report["total"] else 1)
