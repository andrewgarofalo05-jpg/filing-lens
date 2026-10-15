from filing_lens.filings import parse_sections, retrieve


def test_uses_body_instead_of_table_of_contents_and_removes_scripts():
    html = """<a>Item 1. Business</a><a>Item 1A. Risk Factors</a><a>Item 2. Properties</a>
    <h2>Item 1. Business</h2><p>We manufacture industrial tools for customers.</p>
    <h2>Item 1A. Risk Factors</h2><p>Our supply chain depends on a single supplier.
    Supply disruptions can delay production and increase our costs.</p>
    <script>steal secrets</script><h2>Item 2. Properties</h2><p>Our offices are leased.</p>"""
    sections = parse_sections(html)
    risk = next(x for x in sections if x.item == "1A")
    assert "single supplier" in risk.text
    assert "steal secrets" not in risk.text
    evidence = retrieve(sections, "What supply chain disruptions affect production?")
    assert evidence and evidence[0].item == "1A"
    assert evidence[0].text in risk.text


def test_abstains_for_unrelated_question():
    sections = parse_sections("<h2>Item 1. Business</h2><p>We manufacture tools.</p>")
    assert retrieve(sections, "What are quantum gravity predictions?") == []


def test_no_heading_is_explicitly_unclassified():
    sections = parse_sections("<p>A supplier disruption might affect manufacturing.</p>")
    assert sections[0].item == "Unclassified"
