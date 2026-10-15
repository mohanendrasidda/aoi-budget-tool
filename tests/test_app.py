from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


def _run():
    return AppTest.from_file(str(APP), default_timeout=30).run()


def test_app_renders_estimate_without_errors():
    at = _run()
    assert not at.exception
    assert at.metric[0].label == "Budget range"
    assert at.metric[0].value.startswith("\\$")  # escaped so Streamlit does not render LaTeX
    assert "Preliminary furniture budget" in at.code[0].value


def test_app_survives_public_buyer_with_adders():
    at = _run()
    at.radio(key="buyer").set_value("public")
    at.checkbox(key="adders").check()
    at.run()
    assert not at.exception


def test_refresh_shows_reuse_and_lowers_the_range():
    at = _run()
    before = at.metric[0].value
    at.radio(key="ptype").set_value("Refresh").run()
    assert not at.exception
    assert at.slider(key="reuse").value == 25
    assert at.metric[0].value != before
    assert "25% of furniture reused" in at.code[0].value


def test_notes_are_kept_as_plain_text():
    at = _run()
    at.text_area(key="notes").input("<script>alert(1)</script> 40 people").run()
    assert not at.exception
    assert any("<script>" in t.value for t in at.text)  # shown verbatim as text, never as HTML
    assert not any("<script>" in m.value for m in at.markdown)
