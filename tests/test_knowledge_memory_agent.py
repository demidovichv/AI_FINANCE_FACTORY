from pathlib import Path

import pytest

from agents.knowledge_memory_agent import KnowledgeMemoryAgent
from agents.lock_manager import LockManager
from agents.obsidian_parser import write
from agents.shared_models import Article, Keyword


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
def temp_lock_dir(tmp_path: Path) -> Path:
    return tmp_path / ".locks"


def _seed_article(temp_obsidian: Path, article_id: str, title: str) -> None:
    article = Article(
        id=article_id,
        offer_id="offer_test",
        title=title,
        status="draft",
        content=f"# {title}\n\nBody.",
    )
    write(article, "article")


def _seed_keyword(temp_obsidian: Path, kw_id: str, text: str) -> None:
    kw = Keyword(
        id=kw_id,
        text=text,
        intent="informational",
    )
    write(kw, "keyword")


def test_check_uniqueness_duplicate_article(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    _seed_article(temp_obsidian, "article_001", "Детские карты Альфа-Банк")
    agent = KnowledgeMemoryAgent(lock_manager=LockManager(lock_dir=str(temp_lock_dir)))
    result = agent.check_uniqueness("карта для ребенка")
    assert result["status"] == "duplicate"
    assert "article_001" in result["message"]
    assert len(result["matches"]) > 0


def test_check_uniqueness_unique_keyword(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    _seed_article(temp_obsidian, "article_001", "Детские карты Альфа-Банк")
    agent = KnowledgeMemoryAgent(lock_manager=LockManager(lock_dir=str(temp_lock_dir)))
    result = agent.check_uniqueness("ипотека")
    assert result["status"] == "unique"
    assert result["message"] == "OK"


def test_check_uniqueness_similar_keyword(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    _seed_keyword(temp_obsidian, "kw_child", "детская карта")
    agent = KnowledgeMemoryAgent(lock_manager=LockManager(lock_dir=str(temp_lock_dir)))
    result = agent.check_uniqueness("детские карты отзывы")
    assert result["status"] == "duplicate"
    assert "kw_child" in result["message"]
