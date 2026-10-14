from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


def test_app_renders_estimate_without_errors():
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not at.exception
    assert at.metric[0].label == "Budget range"


def test_app_survives_public_buyer_with_adders():
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    at.radio(key="buyer").set_value("public")
    at.checkbox(key="adders").check()
    at.run()
    assert not at.exception
