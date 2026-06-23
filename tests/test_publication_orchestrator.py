from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agents.lock_manager import LockManager
from agents.obsidian_parser import write
from agents.publication_orchestrator import PublicationOrchestrator
from agents.review_manager import ReviewManager
from agents.shared_models import Article, Pin


@pytest.fixture()
def temp_obsidian(tmp_path: Path) -> Path:
    root = tmp_path / "Obsidian"
    (root / "Articles" / "drafts").mkdir(parents=True)
    (root / "Articles" / "html").mkdir(parents=True)
    (root / "Offers").mkdir()
    (root / "Keywords").mkdir(parents=True)
    (root / "Clusters").mkdir()
    (root / "Pins").mkdir()
    (root / "Telegram").mkdir()
    (root / "YouTube").mkdir()
    (root / "Email").mkdir()
    (root / "Reports").mkdir()
    import agents.obsidian_parser as parser
    parser._OBSIDIAN_ROOT = root
    return root


@pytest.fixture()
def temp_roots(tmp_path: Path):
    review = tmp_path / "Review_Queue"
    exports = tmp_path / "Exports"
    logs = tmp_path / "Logs"
    rm = ReviewManager(
        review_root=str(review),
        exports_root=str(exports),
        lock_manager=LockManager(lock_dir=str(tmp_path / ".locks")),
    )
    (tmp_path / "Logs").mkdir(parents=True, exist_ok=True)
    return rm, tmp_path


def _make_article() -> Article:
    return Article(
        id="article_001",
        offer_id="offer_test",
        title="Детская карта Альфа-Банк",
        status="draft",
    )


def _make_pin(temp_obsidian: Path) -> Pin:
    pin = Pin(
        id="pin_001",
        article_id="article_001",
        title="Тестовый пин",
        description="Описание",
        image_prompt="prompt",
        board="myfinq_articles",
        status="draft",
    )
    write(pin, "pin")
    return pin


def _create_html(tmp_path: Path, name: str = "article_001.html") -> Path:
    src = tmp_path / "Exports" / name
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("<html><body>test</body></html>", encoding="utf-8")
    return src


def test_approve_article_success(
    temp_obsidian: Path,
    temp_roots
) -> None:
    rm, tmp_path = temp_roots
    article = _make_article()
    write(article, "article")
    src = _create_html(tmp_path)
    rm.submit_for_review("article_001", "article", src)
    
    github_mock = MagicMock()
    github_mock.publish_approved_articles.return_value = ["article_001"]
    
    orchestrator = PublicationOrchestrator(
        review_manager=rm,
        github_publisher=github_mock,
        log_path=str(tmp_path / "Logs" / "publication_log.md"),
    )
    
    result = orchestrator.process_approval("article_001", "article")
    
    assert result["status"] == "success"
    assert github_mock.publish_approved_articles.called


def test_approve_pin_success(
    temp_obsidian: Path,
    temp_roots
) -> None:
    rm, tmp_path = temp_roots
    pin = _make_pin(temp_obsidian)
    
    uploader_mock = MagicMock()
    uploader_mock.upload_pin.return_value = True
    
    orchestrator = PublicationOrchestrator(
        review_manager=rm,
        pinterest_uploader=uploader_mock,
        log_path=str(tmp_path / "Logs" / "publication_log.md"),
    )
    
    dummy_src = tmp_path / "dummy.png"
    dummy_src.write_bytes(b"")
    rm.submit_for_review("pin_001", "pin", dummy_src)
    
    result = orchestrator.process_approval("pin_001", "pin", image_path=dummy_src)
    
    assert result["status"] == "success"
    assert uploader_mock.upload_pin.called


def test_approve_telegram_skips_publish(
    temp_obsidian: Path,
    temp_roots
) -> None:
    rm, tmp_path = temp_roots
    dummy_src = tmp_path / "dummy.txt"
    dummy_src.write_text("telegram", encoding="utf-8")
    rm.submit_for_review("tg_001", "telegram_post", dummy_src)
    
    orchestrator = PublicationOrchestrator(
        review_manager=rm,
        log_path=str(tmp_path / "Logs" / "publication_log.md"),
    )
    
    result = orchestrator.process_approval("tg_001", "telegram_post")
    
    assert result["status"] == "success"
    assert any(
        step["stage"] == "telegram_ready" for step in result["steps"]
    )


def test_publish_failure_handling(
    temp_obsidian: Path,
    temp_roots
) -> None:
    rm, tmp_path = temp_roots
    article = _make_article()
    write(article, "article")
    src = _create_html(tmp_path)
    rm.submit_for_review("article_001", "article", src)
    
    github_mock = MagicMock()
    github_mock.publish_approved_articles.side_effect = RuntimeError("Git error")
    
    orchestrator = PublicationOrchestrator(
        review_manager=rm,
        github_publisher=github_mock,
        log_path=str(tmp_path / "Logs" / "publication_log.md"),
    )
    
    result = orchestrator.process_approval("article_001", "article")
    
    assert result["status"] == "failed"
    assert any(
        step["stage"] == "publish" and step["status"] == "failed"
        for step in result["steps"]
    )
