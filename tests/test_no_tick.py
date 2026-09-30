from pathlib import Path


def test_project_does_not_implement_tick_data():
    root = Path(__file__).resolve().parents[1] / "src" / "ashare_data"
    forbidden = ["transaction(", "tencent_ticks", "逐笔成交"]
    text = "\n".join(p.read_text(encoding="utf-8") for p in root.rglob("*.py"))
    for token in forbidden:
        assert token not in text

