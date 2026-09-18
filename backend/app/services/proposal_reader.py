from pathlib import Path
from app.core.config import settings
from app.models.requests import ProposalInfo


def read_text_file(path: Path | str) -> str:
    """Read a text or markdown file with UTF-8 encoding."""
    target_path = Path(path)
    if not target_path.exists():
        raise FileNotFoundError(f"File not found: {target_path}")
    return target_path.read_text(encoding="utf-8")


def resolve_proposal_path(filename: str) -> Path:
    """Resolve a proposal filename safely against configured proposal directories.
    
    Prevents directory traversal attacks by taking only the filename's basename.
    """
    safe_name = Path(filename).name
    candidate_names = [safe_name]
    if not safe_name.endswith(".md"):
        candidate_names.append(f"{safe_name}.md")

    search_dirs = [
        settings.PROPOSALS_DIR,
        settings.BACKEND_DIR / "data" / "response",
        settings.PROJECT_ROOT / "response",
    ]

    for directory in search_dirs:
        if directory.exists():
            for name in candidate_names:
                candidate_path = directory / name
                if candidate_path.is_file():
                    return candidate_path

    raise FileNotFoundError(f"Proposal file '{safe_name}' not found in {settings.PROPOSALS_DIR}")


def list_available_proposals() -> list[ProposalInfo]:
    """Scan configured proposals directory and return available proposal files."""
    proposals_dir = settings.PROPOSALS_DIR
    if not proposals_dir.exists():
        # Fallback to root response
        fallback_dir = settings.PROJECT_ROOT / "response"
        if fallback_dir.exists():
            proposals_dir = fallback_dir

    if not proposals_dir.exists():
        return []

    results: list[ProposalInfo] = []
    for file_path in sorted(proposals_dir.glob("*.md")):
        # Generate friendly title from filename: response_1_weak.md -> Response 1 Weak
        display_title = file_path.stem.replace("_", " ").title()
        results.append(
            ProposalInfo(
                filename=file_path.name,
                title=display_title,
                size_bytes=file_path.stat().st_size,
            )
        )

    return results