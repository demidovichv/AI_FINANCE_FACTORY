from pathlib import Path

import pytest

from agents.keyword_researcher import KeywordResearcher
from agents.lock_manager import LockManager
from agents.obsidian_parser import read
from agents.shared_models import Offer


@pytest.fixture()
def temp_obsidian(tmp_path: Path) -> Path:
    root = tmp_path / "Obsidian"
    (root / "Keywords").mkdir(parents=True)
    (root / "Offers").mkdir()
    (root / "Articles" / "drafts").mkdir(parents=True)
    (root / "Articles" / "html").mkdir(parents=True)
    (root / "Pins").mkdir()
    (root / "Telegram").mkdir()
    (root / "YouTube").mkdir()
    (root / "Email").mkdir()
    (root / "Clusters").mkdir()
    (root / "Reports").mkdir()
    import agents.obsidian_parser as parser
    parser._OBSIDIAN_ROOT = root
    return root


@pytest.fixture()
def temp_lock_dir(tmp_path: Path) -> Path:
    return tmp_path / ".locks"


def test_research_generates_keywords(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    offer = Offer(
        id="offer_test",
        name="Детская карта Альфа-Банк",
        bank="Альфа-Банк",
        offer_url="https://example.com",
        status="active",
    )
    lm = LockManager(lock_dir=str(temp_lock_dir))
    researcher = KeywordResearcher(lock_manager=lm)
    keywords = researcher.research(offer)
    assert len(keywords) >= 5
    for kw in keywords:
        assert kw.id.startswith("kw_")
        assert kw.text
        assert kw.intent in {"informational", "commercial", "transactional"}


def test_saved_keywords_exist_in_obsidian(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    offer = Offer(
        id="offer_alfa",
        name="Карта Альфа-Банка",
        bank="Альфа-Банк",
        offer_url="https://example.com",
        status="active",
    )
    lm = LockManager(lock_dir=str(temp_lock_dir))
    researcher = KeywordResearcher(lock_manager=lm)
    keywords = researcher.research(offer)
    assert len(keywords) >= 5
    for kw in keywords:
        loaded = read("keyword", kw.id)
        assert loaded.id == kw.id
        assert loaded.text == kw.text
        assert loaded.intent == kw.intent
