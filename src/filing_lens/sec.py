"""Bounded SEC reads. Cache contains public responses, never contact details."""

import hashlib
import json
import re
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import requests

from filing_lens.models import Filing

MAX_BYTES = 25 * 1024 * 1024
CACHE_TTL = 24 * 60 * 60
_LOCK = threading.Lock()
_LAST_REQUEST = 0.0
_BLOCKED_UNTIL = 0.0


class SecError(RuntimeError):
    """A safe, user-facing SEC access error."""


@dataclass(frozen=True)
class FetchResult:
    content: str
    fetched_at: str
    cached: bool


def filing_url(cik: str, accession: str, document: str) -> str:
    if not re.fullmatch(r"\d{1,10}", str(cik)) or int(cik) == 0:
        raise ValueError("CIK must contain 1–10 digits and be positive.")
    if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
        raise ValueError("Invalid accession number.")
    if not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*\.html?", document):
        raise ValueError("Invalid primary document name.")
    folder = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{folder}/{document}"


def validate_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.query or parsed.fragment:
        raise ValueError("Only canonical SEC URLs are allowed.")
    allowed = (
        parsed.netloc == "data.sec.gov"
        and re.fullmatch(
            r"/(submissions/CIK\d{10}|api/xbrl/companyfacts/CIK\d{10})\.json", parsed.path
        )
    ) or (
        parsed.netloc == "www.sec.gov"
        and (
            parsed.path == "/files/company_tickers.json"
            or re.fullmatch(
                r"/Archives/edgar/data/\d{1,10}/\d{18}/[A-Za-z0-9_-][A-Za-z0-9_.-]*\.html?",
                parsed.path,
            )
        )
    )
    if not allowed:
        raise ValueError("URL is outside the permitted SEC endpoints.")


class SecClient:
    def __init__(self, contact: str, cache_dir: Path | str = ".cache/sec"):
        if not re.fullmatch(r"[^\r\n]{2,100}\s+[^\s@]+@[^\s@]+\.[^\s@]+", contact.strip()):
            raise ValueError("Enter a name and contact email, such as Jane Doe jane@school.edu.")
        self.cache_dir = Path(cache_dir)
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": f"FilingLens/0.1 {contact.strip()}", "Accept-Encoding": "gzip, deflate"}
        )

    @staticmethod
    def _pace():
        global _LAST_REQUEST
        with _LOCK:
            if time.monotonic() < _BLOCKED_UNTIL:
                raise SecError("SEC cooldown is active. Wait before trying again; use the demo.")
            delay = 0.6 - (time.monotonic() - _LAST_REQUEST)
            if delay > 0:
                time.sleep(delay)
            _LAST_REQUEST = time.monotonic()

    def fetch(self, url: str) -> FetchResult:
        global _BLOCKED_UNTIL
        validate_url(url)
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache_dir / f"{key}.json"
        if path.exists() and path.stat().st_size <= MAX_BYTES * 2:
            try:
                cached = json.loads(path.read_text(encoding="utf-8"))
                age = time.time() - cached["timestamp"]
                if 0 <= age < CACHE_TTL and isinstance(cached["content"], str):
                    return FetchResult(cached["content"], cached["fetched_at"], True)
            except (ValueError, KeyError, TypeError, OSError):
                pass  # A corrupt cache is not evidence; fetch a fresh copy.
        for attempt in range(3):
            self._pace()
            response = None
            try:
                response = self.session.get(
                    url, timeout=(5, 30), stream=True, allow_redirects=False
                )
                if response.status_code in (403, 429):
                    # Respect Retry-After (seconds or HTTP date); do not retry a block.
                    retry = response.headers.get("Retry-After", "600")
                    try:
                        seconds = float(retry)
                    except ValueError:
                        from email.utils import parsedate_to_datetime

                        try:
                            seconds = parsedate_to_datetime(retry).timestamp() - time.time()
                        except (ValueError, TypeError, OverflowError):
                            seconds = 600
                    with _LOCK:
                        _BLOCKED_UNTIL = time.monotonic() + max(600, seconds)
                    raise SecError(
                        "SEC access is temporarily blocked (403/429). "
                        "A cooldown of at least 10 minutes is active. Use the demo."
                    )
                if response.status_code in (500, 502, 503, 504) and attempt < 2:
                    time.sleep(2**attempt)
                    continue
                if response.status_code != 200:
                    raise SecError(
                        f"SEC returned HTTP {response.status_code}. "
                        "No redirect or bypass was attempted."
                    )
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise SecError("SEC response exceeds the 25 MB safety limit.")
                    chunks.append(chunk)
                content = b"".join(chunks).decode("utf-8", errors="replace")
                fetched_at = datetime.now(UTC).isoformat()
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                # Unique temporary names avoid cross-session partial cache reads.
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", delete=False, dir=self.cache_dir, suffix=".tmp"
                ) as temp:
                    json.dump(
                        dict(content=content, fetched_at=fetched_at, timestamp=time.time()), temp
                    )
                Path(temp.name).replace(path)
                return FetchResult(content, fetched_at, False)
            except requests.RequestException as exc:
                if attempt == 2:
                    raise SecError(
                        "SEC request timed out or could not connect. Use the demo."
                    ) from exc
                time.sleep(2**attempt)
            finally:
                if response is not None:
                    response.close()
        raise SecError("SEC request failed.")

    def json(self, url: str) -> dict:
        try:
            result = json.loads(self.fetch(url).content)
        except ValueError as exc:
            raise SecError("SEC returned a non-JSON response. Try later.") from exc
        if not isinstance(result, dict):
            raise SecError("Unexpected SEC response structure.")
        return result

    def resolve(self, identifier: str) -> str:
        identifier = identifier.strip().upper()
        if re.fullmatch(r"\d{1,10}", identifier) and int(identifier) > 0:
            return identifier.zfill(10)
        if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", identifier):
            raise ValueError("Enter a ticker (AAPL) or a numeric CIK (320193).")
        companies = self.json("https://www.sec.gov/files/company_tickers.json")
        for company in companies.values():
            if company.get("ticker", "").upper() == identifier:
                return str(company["cik_str"]).zfill(10)
        raise ValueError("Ticker not found. Try the company's CIK from SEC EDGAR.")


def recent_filings(data: dict) -> list[Filing]:
    recent = data.get("filings", {}).get("recent", {})
    filings = []
    try:
        for i, form in enumerate(recent.get("form", [])):
            if form != "10-K":
                continue
            accession, document = recent["accessionNumber"][i], recent["primaryDocument"][i]
            filings.append(
                Filing(
                    str(data["cik"]).zfill(10),
                    data["name"],
                    accession,
                    recent["filingDate"][i],
                    recent["reportDate"][i],
                    document,
                    filing_url(str(data["cik"]), accession, document),
                )
            )
    except (KeyError, IndexError, TypeError) as exc:
        raise SecError("Unexpected SEC submissions structure.") from exc
    return sorted(filings, key=lambda filing: filing.filed, reverse=True)[:10]
