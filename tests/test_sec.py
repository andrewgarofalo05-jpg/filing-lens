import json
from unittest.mock import Mock

import pytest

from filing_lens.sec import SecClient, SecError, filing_url, recent_filings


def response(body=b"{}", status=200):
    result = Mock(status_code=status, headers={})
    result.iter_content.return_value = [body]
    return result


def test_validates_contact_and_blocks_arbitrary_hosts(tmp_path):
    with pytest.raises(ValueError):
        SecClient("", tmp_path)
    client = SecClient("Student student@example.org", tmp_path)
    with pytest.raises(ValueError):
        client.fetch("https://evil.example/data")


def test_cache_avoids_duplicate_network_access(tmp_path, monkeypatch):
    client = SecClient("Student student@example.org", tmp_path)
    monkeypatch.setattr(client, "_pace", lambda: None)
    client.session.get = Mock(return_value=response(b'{"name":"Example"}'))
    url = "https://data.sec.gov/submissions/CIK0000320193.json"
    assert json.loads(client.fetch(url).content)["name"] == "Example"
    assert client.fetch(url).cached
    assert client.session.get.call_count == 1


@pytest.mark.parametrize("status", [301, 403, 404])
def test_blocked_redirect_or_missing_response_is_not_retried(tmp_path, monkeypatch, status):
    client = SecClient("Student student@example.org", tmp_path)
    monkeypatch.setattr(client, "_pace", lambda: None)
    client.session.get = Mock(return_value=response(status=status))
    with pytest.raises(SecError):
        client.fetch("https://data.sec.gov/submissions/CIK0000320193.json")
    assert client.session.get.call_count == 1


def test_rejects_path_traversal():
    with pytest.raises(ValueError):
        filing_url("320193", "0000320193-24-000123", "../../secret")


def test_only_original_ten_ks_are_listed():
    data = {
        "cik": "320193",
        "name": "Apple",
        "filings": {
            "recent": {
                "form": ["10-K/A", "10-K"],
                "accessionNumber": ["0000320193-24-000124", "0000320193-24-000123"],
                "filingDate": ["2024-11-02", "2024-11-01"],
                "reportDate": ["2024-09-28", "2024-09-28"],
                "primaryDocument": ["amend.htm", "aapl-20240928.htm"],
            }
        },
    }
    result = recent_filings(data)
    assert len(result) == 1 and result[0].accession.endswith("000123")
