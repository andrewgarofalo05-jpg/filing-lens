"""Heuristic item segmentation and transparent local lexical evidence retrieval."""

import hashlib
import math
import re
from collections import Counter

from bs4 import BeautifulSoup

from filing_lens.models import Passage, Section

TITLES = {
    "1": "Business",
    "1A": "Risk Factors",
    "1B": "Unresolved Staff Comments",
    "1C": "Cybersecurity",
    "2": "Properties",
    "3": "Legal Proceedings",
    "4": "Mine Safety Disclosures",
    "5": "Market for Common Equity",
    "6": "Reserved",
    "7": "Management’s Discussion and Analysis",
    "7A": "Market Risk",
    "8": "Financial Statements and Supplementary Data",
    "9": "Changes in Accountants",
    "9A": "Controls and Procedures",
    "9B": "Other Information",
    "9C": "Foreign Jurisdictions",
    "10": "Directors and Governance",
    "11": "Executive Compensation",
    "12": "Security Ownership",
    "13": "Related Transactions",
    "14": "Accountant Fees",
    "15": "Exhibits",
    "16": "Form 10-K Summary",
}
STOPWORDS = set(
    "what which how does do the a an is are was were to of in on and or for "
    "with by from it its this that company companies about tell me explain "
    "please their has have can could would should risks risk".split()
)
HEADING = re.compile(r"(?im)^\s*item\s+(1[0-6]|[1-9])([abc]?)\s*[.:—\-]?\s*")


def parse_sections(html: str) -> list[Section]:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.find_all(["script", "style", "noscript", "ix:header", "head"]):
        node.decompose()
    for node in soup.find_all(attrs={"hidden": True}):
        node.decompose()
    # Preserve inline heading spans but separate block elements, as in real inline XBRL.
    for node in soup.find_all(["p", "div", "h1", "h2", "h3", "h4", "tr", "br", "li"]):
        node.insert_before("\n")
        node.insert_after("\n")
    text = soup.get_text(" ").replace("\xa0", " ")
    text = "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines())
    matches = list(HEADING.finditer(text))
    if not matches:
        return [Section("Unclassified", "Section not detected — verify in original", text.strip())]
    candidates: dict[str, Section] = {}
    for index, match in enumerate(matches):
        item = (match.group(1) + match.group(2)).upper()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        section = Section(item, TITLES.get(item, f"Item {item}"), body)
        # TOC entries are generally shorter than the actual section. This is a heuristic.
        if item not in candidates or len(body) > len(candidates[item].text):
            candidates[item] = section
    return list(candidates.values())


def tokens(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z]{3,}", text.lower()) if word not in STOPWORDS]


def retrieve(sections: list[Section], question: str, limit: int = 3) -> list[Passage]:
    """Return exact contiguous chunks, not generated answers or confidence scores."""
    if len(question) > 1000:
        raise ValueError("Keep questions under 1,000 characters.")
    query = set(tokens(question))
    if not query:
        return []
    chunks = []
    for section in sections:
        # Paragraph boundaries preserve exact excerpts; oversized paragraphs use word breaks.
        for paragraph in re.split(r"\n+", section.text):
            paragraph = paragraph.strip()
            while paragraph:
                cut = len(paragraph) if len(paragraph) <= 1200 else paragraph.rfind(" ", 0, 1200)
                if cut <= 0:
                    cut = min(1200, len(paragraph))
                chunk, paragraph = paragraph[:cut], paragraph[cut:].lstrip()
                if len(chunk) >= 30:
                    chunks.append((section, chunk, Counter(tokens(chunk))))
    counts = Counter(word for _, _, words in chunks for word in words)
    ranked = []
    for section, chunk, words in chunks:
        overlap = query & words.keys()
        if not overlap or len(overlap) / len(query) < 0.25:
            continue
        score = sum(
            (1 + math.log((1 + len(chunks)) / (1 + counts[w]))) * words[w] / (words[w] + 1.2)
            for w in overlap
        )
        digest = hashlib.sha256((section.item + "\n" + chunk).encode()).hexdigest()[:10]
        ranked.append(Passage("P" + digest, section.item, section.title, chunk, score))
    return sorted(ranked, key=lambda p: (-p.score, p.id))[:limit]
