from pathlib import Path
import pathspec
from typing import Any

EXTENSIONS = [".py", ".js", ".ts", ".go", ".rs", ".java"]


def load_gitignore(repo_root: Path) -> Any:
    print(f"Type of repo_root: {type(repo_root)}")
    print(f"Value of repo_root: {repo_root}")
    gitignore = repo_root / ".gitignore"

    if not gitignore.exists():
        return pathspec.PathSpec.from_lines("gitwildmatch", [])

    return pathspec.PathSpec.from_lines(
        "gitwildmatch",
        gitignore.read_text().splitlines(),
    )


def scan_repo(path: str) -> list[Path]:
    root = Path(path)
    spec: Any = load_gitignore(root)

    files: list[Path] = []

    for p in root.rglob("*"):
        rel_path = p.relative_to(root)

        if spec.match_file(str(rel_path)):
            continue

        if p.is_file() and p.suffix in EXTENSIONS:
            files.append(p)

    return files