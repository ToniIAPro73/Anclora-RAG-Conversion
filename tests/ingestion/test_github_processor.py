from __future__ import annotations

import asyncio
from pathlib import Path

from app.ingestion.github_processor import GitHubRepositoryProcessor, RepositoryOptions


def test_github_processor_filters_repository(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "README.md").write_text("Documentacion")
    (repo_dir / "src").mkdir()
    (repo_dir / "src" / "main.py").write_text("print('hello')")
    (repo_dir / "node_modules").mkdir()
    (repo_dir / "node_modules" / "ignored.js").write_text("console.log('skip')")
    large_file = repo_dir / "large.bin"
    large_file.write_bytes(b"0" * (30 * 1024 * 1024))

    processor = GitHubRepositoryProcessor()
    options = RepositoryOptions(max_file_size_mb=10)

    files = asyncio.run(processor.gather_repository_files(str(repo_dir), options))
    relative_paths = {item["relative_path"] for item in files}

    assert "README.md" in relative_paths
    assert "src/main.py" in relative_paths
    assert all(not path.startswith("node_modules/") for path in relative_paths)
    assert all(item["size"] <= 10 * 1024 * 1024 for item in files)
