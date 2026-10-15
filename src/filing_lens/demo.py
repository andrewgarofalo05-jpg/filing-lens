"""Small, hand-curated offline example. It is NOT a downloaded Company Facts payload."""

from importlib.resources import files

from filing_lens.filings import parse_sections
from filing_lens.models import Filing

ACC = "0000320193-24-000123"
URL = "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm"


def load_demo() -> dict:
    html = files("filing_lens").joinpath("data/demo.html").read_text(encoding="utf-8")
    # Transcribed from Item 8, Consolidated Statements of Operations, page 29.
    # The original table is in millions of USD. Values below are full USD.
    values = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": (383285, 391035),
        "NetIncomeLoss": (96995, 93736),
        "OperatingIncomeLoss": (114301, 123216),
    }
    concepts = {}
    periods = [("2022-09-25", "2023-09-30"), ("2023-10-01", "2024-09-28")]
    for tag, amounts in values.items():
        concepts[tag] = {
            "units": {
                "USD": [
                    dict(
                        start=start,
                        end=end,
                        val=amount * 1_000_000,
                        accn=ACC,
                        form="10-K",
                        filed="2024-11-01",
                        fy=2024,
                        fp="FY",
                    )
                    for (start, end), amount in zip(periods, amounts, strict=True)
                ]
            }
        }
    return {
        "filing": Filing(
            "0000320193", "Apple Inc.", ACC, "2024-11-01", "2024-09-28", "aapl-20240928.htm", URL
        ),
        "sections": parse_sections(html),
        "facts": {"facts": {"us-gaap": concepts}},
        "filing_fetched_at": "Hand-curated demo; verified 2026-10-15",
        "facts_fetched_at": "Manually transcribed from Item 8; verified 2026-10-15",
        "demo": True,
    }
