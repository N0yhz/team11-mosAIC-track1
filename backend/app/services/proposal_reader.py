from pathlib import Path


def read_text_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"Datei nicht gefunden: {path}"
        )

    return path.read_text(
        encoding="utf-8"
    )