from decimal import Decimal

import pytest

from filing_lens.financials import compare, select_annual

ACC = "0000320193-24-000123"


def facts(rows, tag="Revenues", unit="USD"):
    return {"facts": {"us-gaap": {tag: {"units": {unit: rows}}}}}


def row(value, start="2023-10-01", end="2024-09-28", **kwargs):
    return dict(
        val=value, start=start, end=end, accn=ACC, form="10-K", filed="2024-11-01", **kwargs
    )


def test_selects_period_not_fiscal_year_label_and_excludes_quarters():
    data = facts(
        [
            row(100, fy=2024),
            row(20, start="2024-07-01", fy=2024),
            row(90, start="2022-09-25", end="2023-09-30", fy=2024),
        ]
    )
    selected = select_annual(data, "Revenue", ACC)
    assert [x.end for x in selected] == ["2023-09-30", "2024-09-28"]
    assert [x.value for x in selected] == [Decimal(90), Decimal(100)]


def test_conflicting_values_are_rejected():
    with pytest.raises(ValueError, match="Conflicting"):
        select_annual(facts([row(100), row(101)]), "Revenue", ACC)


def test_wrong_accession_and_currency_are_not_substituted():
    assert select_annual(facts([row(100)], unit="EUR"), "Revenue", ACC) == []
    assert select_annual(facts([row(100)]), "Revenue", "0000000000-00-000000") == []


def test_deterministic_change_and_growth():
    periods = select_annual(facts([row(110), row(100, "2022-10-01", "2023-09-30")]), "Revenue", ACC)
    result = compare(*periods)
    assert result.change == Decimal(10)
    assert result.percent == Decimal(10)


@pytest.mark.parametrize("baseline", [0, -100])
def test_nonpositive_baseline_has_no_growth_percentage(baseline):
    periods = select_annual(
        facts([row(110), row(baseline, "2022-10-01", "2023-09-30")]), "Revenue", ACC
    )
    assert compare(*periods).percent is None


def test_does_not_mix_revenue_concepts():
    data = facts([row(100)])
    data["facts"]["us-gaap"]["SalesRevenueNet"] = {
        "units": {"USD": [row(90, "2022-10-01", "2023-09-30")]}
    }
    assert len(select_annual(data, "Revenue", ACC)) == 1
