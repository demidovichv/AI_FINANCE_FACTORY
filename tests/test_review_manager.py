from pathlib import Path

import pytest

from agents.lock_manager import LockManager
from agents.review_manager import ReviewManager


@pytest.fixture()
def temp_roots(tmp_path: Path) -> Path:
    review = tmp_path / "Review_Queue"
    exports = tmp_path / "Exports"
    rm = ReviewManager(
        review_root=str(review),
        exports_root=str(exports),
        lock_manager=LockManager(lock_dir=str(tmp_path / ".locks")),
    )
    return rm


def _write_dummy(path: Path, content: str = "<html><body>test</body></html>") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_submit_for_review_creates_files(temp_roots: Path) -> None:
    src = temp_roots.exports_root / "source.html"
    _write_dummy(src, "<h1>Test</h1>")
    status = temp_roots.submit_for_review("entity_01", "article", src)
    assert status.status == "pending"
    assert status.entity_id == "entity_01"
    assert status.entity_type == "article"
    article_queue = temp_roots.review_root / "articles"
    assert (article_queue / "entity_01.html").exists()
    assert (article_queue / "entity_01.json").exists()


def test_approve_moves_to_ready(temp_roots: Path) -> None:
    src = temp_roots.exports_root / "source2.html"
    _write_dummy(src, "<h1>Approve</h1>")
    temp_roots.submit_for_review("entity_02", "article", src)
    approved = temp_roots.approve("entity_02", "article")
    assert approved.status == "approved"
    assert approved.output_path is not None
    assert Path(approved.output_path).exists()
    assert Path(approved.output_path).parent.name == "Ready_To_Publish"


def test_reject_removes_file(temp_roots: Path) -> None:
    src = temp_roots.exports_root / "source3.html"
    _write_dummy(src, "<h1>Reject</h1>")
    temp_roots.submit_for_review("entity_03", "article", src)
    rejected = temp_roots.reject("entity_03", "article", reason="bad quality")
    assert rejected.status == "rejected"
    assert rejected.rejection_reason == "bad quality"
    article_queue = temp_roots.review_root / "articles"
    assert not (article_queue / "entity_03.html").exists()
    assert (article_queue / "entity_03.json").exists()
