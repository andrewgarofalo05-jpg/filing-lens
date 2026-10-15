import json

from filing_lens.research import main


def test_skill_demo_returns_evidence_and_exact_arithmetic(capsys):
    assert (
        main(["--demo", "--question", "What outsourcing partners are used?", "--metric", "Revenue"])
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["demo"] is True
    assert result["evidence"][0]["item"] == "1A"
    assert result["comparison"]["change"] == "7750000000"
    assert result["filing"]["accession"] == "0000320193-24-000123"


def test_skill_missing_contact_fails_without_network(monkeypatch, capsys):
    monkeypatch.delenv("SEC_CONTACT", raising=False)
    assert main(["--company", "AAPL", "--list-filings"]) == 1
    assert "SEC_CONTACT" in json.loads(capsys.readouterr().out)["error"]


def test_skill_unknown_question_returns_no_evidence(capsys):
    assert main(["--demo", "--question", "What are quantum gravity predictions?"]) == 0
    assert json.loads(capsys.readouterr().out)["evidence"] == []
