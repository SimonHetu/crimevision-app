
from pathlib import Path

def apply_theme(app, theme_name: str):
    qss_path = Path(__file__).parent / f"{theme_name}.qss"

    if not qss_path.exists():
        raise ValueError(f"Theme '{theme_name}' not found")

    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
