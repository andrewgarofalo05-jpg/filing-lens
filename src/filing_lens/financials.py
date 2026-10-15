"""Select comparable facts first. Never ask a language model to do arithmetic."""

from datetime import date
from decimal import Decimal, InvalidOperation

from filing_lens.models import Comparison, Fact

# These are alternatives, not interchangeable values to be merged across years.
METRICS = {
    "Revenue": (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ),
    "Net income": ("NetIncomeLoss",),
    "Operating income": ("OperatingIncomeLoss",),
}


def select_annual(data: dict, metric: str, accession: str) -> list[Fact]:
    """Return annual USD duration facts from one original filing and one concept.

    FY labels describe the filing's fiscal year, not each comparative observation.
    Period start/end are therefore authoritative. A 350–380 day window accepts
    ordinary 52/53-week years and excludes quarters and transition periods.
    """
    if metric not in METRICS:
        raise ValueError("Unsupported metric.")
    concepts = data.get("facts", {}).get("us-gaap", {})
    for tag in METRICS[metric]:
        selected: dict[str, Fact] = {}
        for row in concepts.get(tag, {}).get("units", {}).get("USD", []):
            if row.get("accn") != accession or row.get("form") != "10-K":
                continue
            try:
                start, end = date.fromisoformat(row["start"]), date.fromisoformat(row["end"])
                duration = (end - start).days + 1
                if not 350 <= duration <= 380:
                    continue
                value = Decimal(str(row["val"]))
                if not value.is_finite():
                    raise ValueError("Non-finite financial value.")
                fact = Fact(
                    metric,
                    tag,
                    start.isoformat(),
                    end.isoformat(),
                    value,
                    "USD",
                    accession,
                    row["filed"],
                )
            except (KeyError, InvalidOperation, TypeError) as exc:
                raise ValueError(
                    "Malformed annual financial fact; inspect the SEC source."
                ) from exc
            existing = selected.get(fact.end)
            if existing and (existing.value != fact.value or existing.start != fact.start):
                raise ValueError(f"Conflicting annual values for {metric}, {fact.end}.")
            selected[fact.end] = fact
        if selected:
            return sorted(selected.values(), key=lambda x: x.end)
    return []


def compare(prior: Fact, current: Fact) -> Comparison:
    """Compare adjacent years of the same concept, units and filing vintage."""
    if (prior.metric, prior.tag, prior.unit, prior.accession) != (
        current.metric,
        current.tag,
        current.unit,
        current.accession,
    ):
        raise ValueError("Comparison requires the same metric, concept, units and accession.")
    gap = (date.fromisoformat(current.start) - date.fromisoformat(prior.end)).days
    if gap != 1:
        raise ValueError("Comparison requires adjacent, non-overlapping annual periods.")
    change = current.value - prior.value
    percent = change / prior.value * Decimal(100) if prior.value > 0 else None
    warning = ""
    days_prior = (date.fromisoformat(prior.end) - date.fromisoformat(prior.start)).days
    days_current = (date.fromisoformat(current.end) - date.fromisoformat(current.start)).days
    if days_prior != days_current:
        warning = "Reporting periods differ in length; growth is not day-adjusted."
    return Comparison(prior, current, change, percent, warning)
