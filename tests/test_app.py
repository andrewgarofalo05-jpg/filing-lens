from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_demo_renders_and_answers_with_cited_evidence():
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert any("Filing Lens" in t.value for t in app.title)
    app.text_input(key="question").set_value(
        "What outsourcing partners does the company depend on?"
    )
    app.button(key="search").click().run()
    assert not app.exception
    assert any("outsourcing partners" in t.value for t in app.text)
    assert any("1A" in t.label for t in app.expander)


def test_unknown_question_abstains():
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.text_input(key="question").set_value("What are quantum gravity predictions?")
    app.button(key="search").click().run()
    assert not app.exception
    assert any("No supporting passage" in t.value for t in app.warning)


def test_live_mode_requires_identification_without_crashing():
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.radio(key="mode").set_value("Live SEC").run()
    app.button(key="find_company").click().run()
    assert not app.exception
    assert app.error
