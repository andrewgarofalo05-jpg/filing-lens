"""Small immutable records keep provenance attached to the values it describes."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Filing:
    cik: str
    company: str
    accession: str
    filed: str
    report_date: str
    document: str
    url: str


@dataclass(frozen=True)
class Section:
    item: str
    title: str
    text: str


@dataclass(frozen=True)
class Passage:
    id: str
    item: str
    title: str
    text: str
    score: float


@dataclass(frozen=True)
class Fact:
    metric: str
    tag: str
    start: str
    end: str
    value: Decimal
    unit: str
    accession: str
    filed: str


@dataclass(frozen=True)
class Comparison:
    prior: Fact
    current: Fact
    change: Decimal
    percent: Decimal | None
    warning: str
