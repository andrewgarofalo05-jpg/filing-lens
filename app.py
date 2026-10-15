"""Run with: python -m streamlit run app.py"""

import json
from dataclasses import asdict

import requests
import streamlit as st

from filing_lens.demo import load_demo
from filing_lens.filings import parse_sections, retrieve
from filing_lens.financials import METRICS, compare, select_annual
from filing_lens.local_ai import available_models, generate
from filing_lens.sec import SecClient, SecError, recent_filings

st.set_page_config(page_title="Filing Lens | Financial research", page_icon="◈", layout="wide")


def clear_research():
    for key in ("evidence", "draft", "searched_question"):
        st.session_state.pop(key, None)


def show_error(exc):
    st.error(str(exc))


with st.sidebar:
    st.markdown("### ◈ Filing Lens")
    st.caption("FINANCIAL RESEARCH WORKSPACE")
    mode = st.radio("Source", ["Offline demo", "Live SEC"], key="mode")
    if st.session_state.get("previous_mode") != mode:
        clear_research()
        st.session_state["previous_mode"] = mode
    if mode == "Live SEC":
        with st.form("company_form"):
            identifier = st.text_input("Ticker or CIK", value="AAPL", max_chars=10)
            contact = st.text_input(
                "Your name and contact email",
                key="contact",
                max_chars=180,
                help="Required by SEC identification policy. Sent to SEC only.",
            )
            find_company = st.form_submit_button("Find company", key="find_company")
        if find_company:
            # Clear any prior company so a failed lookup cannot display stale results.
            for key in ("live_bundle", "filings", "client"):
                st.session_state.pop(key, None)
            clear_research()
            try:
                client = SecClient(contact)
                cik = client.resolve(identifier)
                data = client.json(f"https://data.sec.gov/submissions/CIK{cik}.json")
                st.session_state["filings"] = recent_filings(data)
                st.session_state["client"] = client
            except (SecError, ValueError, OSError) as exc:
                show_error(exc)
        filings = st.session_state.get("filings", [])
        if filings:
            chosen = st.selectbox(
                "Annual filing", filings, format_func=lambda f: f"{f.report_date} · filed {f.filed}"
            )
            if st.button("Load selected filing", type="primary"):
                st.session_state.pop("live_bundle", None)
                clear_research()
                try:
                    with st.spinner("Reading the filing and structured financial facts…"):
                        client = st.session_state["client"]
                        filing_response = client.fetch(chosen.url)
                        facts_url = (
                            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{chosen.cik}.json"
                        )
                        facts_response = client.fetch(facts_url)
                        facts = json.loads(facts_response.content)
                        if not isinstance(facts, dict) or "facts" not in facts:
                            raise ValueError("SEC returned an unexpected Company Facts response.")
                        st.session_state["live_bundle"] = {
                            "filing": chosen,
                            "sections": parse_sections(filing_response.content),
                            "facts": facts,
                            "demo": False,
                            "filing_fetched_at": filing_response.fetched_at,
                            "facts_fetched_at": facts_response.fetched_at,
                        }
                except (SecError, ValueError, OSError) as exc:
                    show_error(exc)
        elif find_company:
            st.info("No supported recent 10-Ks loaded. Try a domestic US-GAAP filer.")
    st.divider()
    use_ai = st.checkbox("Use a local AI model", value=False)
    selected_model = None
    if use_ai:
        st.caption("Optional Ollama · no paid API. Questions and evidence go to localhost.")
        if st.button("Find installed models"):
            try:
                st.session_state["models"] = available_models()
            except (requests.RequestException, ValueError, KeyError):
                st.session_state["models"] = []
                st.warning(
                    "Ollama is unavailable. See README for setup; evidence search still works."
                )
        models = st.session_state.get("models", [])
        if models:
            selected_model = st.selectbox("Local model", models)
        else:
            st.caption("No local model selected. No model will be downloaded automatically.")
    st.divider()
    st.caption("Research and education only. Not investment advice. Read the original filing.")

st.title("Filing Lens")
st.markdown("#### Read the evidence. Check the numbers.")
st.caption("An AI Financial Research Assistant for grounded, reproducible company research.")

bundle = load_demo() if mode == "Offline demo" else st.session_state.get("live_bundle")
if not bundle:
    st.info("Start with a ticker or CIK in the sidebar, then load an annual filing.")
    st.stop()

filing = bundle["filing"]
if bundle["demo"]:
    st.info(
        "OFFLINE DEMO · Apple FY2024 · One short filing excerpt and six manually transcribed "
        "financial observations. This is not a full filing or current market data."
    )
else:
    st.caption(
        "LIVE SEC SOURCE · Loaded filing shown below; sidebar selection applies when loaded."
    )

company_col, period_col, filed_col = st.columns([2, 1, 1])
company_col.metric("Company", filing.company)
period_col.metric("Report date", filing.report_date)
filed_col.metric("Filed", filing.filed)
st.caption(f"10-K · CIK {filing.cik} · Accession {filing.accession}")

ask_tab, numbers_tab, sources_tab, guide_tab = st.tabs(
    ["Ask the filing", "Compare financials", "Source ledger", "How it works"]
)

with ask_tab:
    st.subheader("Start with a research question")
    st.caption("Try: What outsourcing partners does the company depend on?")
    with st.form("question_form"):
        question = st.text_input(
            "Question about this filing",
            key="question",
            max_chars=1000,
            placeholder="What risks does the filing describe?",
        )
        search = st.form_submit_button("Find supporting evidence", type="primary", key="search")
    if search:
        clear_research()
        st.session_state["searched_question"] = question
        st.session_state["evidence"] = retrieve(bundle["sections"], question)
    if "evidence" in st.session_state:
        evidence = st.session_state["evidence"]
        st.caption("Evidence for: " + st.session_state["searched_question"])
        if not evidence:
            st.warning(
                "No supporting passage found in the loaded text. Try wording from the "
                "filing or load a fuller source. This is not proof the topic is absent."
            )
        else:
            st.success(
                f"{len(evidence)} matching passage(s). "
                "Read the context before drawing a conclusion."
            )
            st.caption(
                "Extractive answer: exact retrieved text, not a generated conclusion. "
                "Section labels are detected heuristically; verify them in the original."
            )
            for passage in evidence:
                with st.expander(
                    f"Item {passage.item} · {passage.title} · {passage.id}", expanded=True
                ):
                    st.text(passage.text)  # Plain text: never execute filing HTML/Markdown.
                    st.link_button("Open original SEC filing", filing.url)
                    st.caption(
                        "Use browser Find for the excerpt. "
                        "This is an item-level citation, with no invented page anchor."
                    )
            export = {
                "question": st.session_state["searched_question"],
                "demo": bundle["demo"],
                "filing": asdict(filing),
                "fetched_at": bundle["filing_fetched_at"],
                "evidence": [asdict(p) for p in evidence],
            }
            st.download_button(
                "Download evidence record",
                json.dumps(export, indent=2),
                "filing-lens-evidence.json",
                "application/json",
            )
            if selected_model and st.button("Draft explanation with local AI"):
                try:
                    with st.spinner("The local model is reading these passages…"):
                        st.session_state["draft"] = generate(
                            st.session_state["searched_question"], evidence, selected_model
                        )
                except (requests.RequestException, ValueError, KeyError) as exc:
                    st.session_state.pop("draft", None)
                    st.warning("AI draft unavailable or rejected: " + str(exc))
            if "draft" in st.session_state:
                st.warning(
                    "AI DRAFT — unverified interpretation. Citation checks verify IDs, "
                    "not meaning. Use Compare financials for every calculation."
                )
                if not st.session_state["draft"]:
                    st.info("The model declined to answer from the available evidence.")
                for claim in st.session_state["draft"]:
                    st.text(claim["text"])
                    st.caption("Evidence: " + ", ".join(claim["citations"]))

with numbers_tab:
    st.subheader("Annual financial comparison")
    st.caption("Deterministic calculations · USD · Same filing and accounting concept")
    metric = st.selectbox("Metric", list(METRICS))
    try:
        observations = select_annual(bundle["facts"], metric, filing.accession)
        if len(observations) < 2:
            st.warning(
                "Fewer than two compatible annual USD facts in this filing. "
                "Custom tags and missing concepts are not guessed."
            )
        else:
            pair = st.selectbox(
                "Reporting periods",
                list(range(1, len(observations))),
                index=len(observations) - 2,
                format_func=lambda i: f"{observations[i - 1].end} → {observations[i].end}",
            )
            comparison = compare(observations[pair - 1], observations[pair])
            prior, current = comparison.prior, comparison.current
            cols = st.columns(3)
            cols[0].metric("Prior period · USD billions", f"${prior.value / 10**9:,.3f}")
            cols[1].metric("Current period · USD billions", f"${current.value / 10**9:,.3f}")
            cols[2].metric(
                "Change",
                "Not meaningful" if comparison.percent is None else f"{comparison.percent:+.2f}%",
            )
            if comparison.warning:
                st.warning(comparison.warning)
            if comparison.percent is None:
                st.info(
                    "Ordinary percentage growth is omitted "
                    "when the prior value is zero or negative."
                )
            st.text(f"Absolute change: ${comparison.change:,.0f} USD")
            st.caption("Formula: (current − prior) ÷ prior × 100, only when prior > 0.")
            st.dataframe(
                [
                    {
                        "Period start": f.start,
                        "Period end": f.end,
                        "Value (exact USD)": f"{f.value:,.0f}",
                        "US-GAAP concept": f.tag,
                        "Accession": f.accession,
                    }
                    for f in (prior, current)
                ],
                hide_index=True,
                width="stretch",
            )
            st.link_button("Verify in Item 8 — Financial Statements", filing.url)
            st.caption(
                "Dates are reporting periods, not calendar-year assumptions. Older figures "
                "are as presented in the selected filing and may reflect restatements."
            )
            record = {
                "demo": bundle["demo"],
                "filing": asdict(filing),
                "facts_fetched_at": bundle["facts_fetched_at"],
                "comparison": asdict(comparison),
            }
            st.download_button(
                "Download comparison record",
                json.dumps(record, indent=2, default=str),
                "filing-lens-comparison.json",
                "application/json",
            )
    except ValueError as exc:
        st.warning(str(exc))

with sources_tab:
    st.subheader("Your source ledger")
    st.link_button("Read this filing on SEC EDGAR", filing.url)
    st.text(
        f"Accession: {filing.accession}\nFiling date: {filing.filed}\n"
        f"Report date: {filing.report_date}\nFiling retrieved: {bundle['filing_fetched_at']}\n"
        f"Facts retrieved: {bundle['facts_fetched_at']}"
    )
    if bundle["demo"]:
        st.caption(
            "Demo provenance: Item 1A, page 8 (one short excerpt); Item 8, page 29 "
            "(six financial observations manually converted from millions to USD). "
            "Concept names are assigned for the demonstration, not fetched XBRL metadata."
        )
    else:
        st.link_button(
            "SEC Company Facts JSON",
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{filing.cik}.json",
        )
    st.write("Detected sections")
    st.dataframe(
        [{"Item": s.item, "Title": s.title, "Characters": len(s.text)} for s in bundle["sections"]],
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "The section parser is heuristic. Missing or mislabeled sections need manual review."
    )

with guide_tab:
    st.subheader("A small research workflow you can audit")
    st.markdown(
        "1. **Choose a filing.** Confirm company, report date and accession.\n"
        "2. **Retrieve evidence.** Search ranks matching passages locally.\n"
        "3. **Check the source.** Open the filing and read surrounding context.\n"
        "4. **Compare facts.** Python selects annual facts and calculates changes.\n"
        "5. **Optionally draft with AI.** A local model explains retrieved text; verify it."
    )
    st.info(
        "Privacy: questions stay in session memory unless you download a record. SEC receives "
        "your contact header and requested filing URLs. Optional AI receives the question "
        "and selected passages through local Ollama. No paid-provider requests are made."
    )
    st.caption(
        "Not investment advice. No recommendations, price forecasts or trading features. "
        "This v1 supports recent original US-GAAP 10-Ks and three annual income-statement metrics."
    )

st.divider()
st.caption(
    "FILING LENS · Evidence before conclusions · Educational research, not investment advice"
)
