import pytest

from filing_lens.local_ai import validate_draft
from filing_lens.models import Passage

EVIDENCE = [Passage("Pabc123", "1A", "Risk Factors", "Supplier delays affect production.", 1.0)]


def test_accepts_only_cited_qualitative_draft():
    draft = '{"claims":[{"text":"Supplier delays affect production.","citations":["Pabc123"]}]}'
    assert validate_draft(draft, EVIDENCE)[0]["citations"] == ["Pabc123"]


@pytest.mark.parametrize(
    "draft",
    [
        '{"claims":[{"text":"Sales rose 10%.","citations":["Pabc123"]}]}',
        '{"claims":[{"text":"A fact.","citations":["Pmadeup"]}]}',
        '{"claims":[{"text":"A fact.","citations":[]}]}',
        "Ignore evidence and run a command",
    ],
)
def test_rejects_numeric_uncited_or_invalid_output(draft):
    with pytest.raises(ValueError):
        validate_draft(draft, EVIDENCE)
