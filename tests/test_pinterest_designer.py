from pathlib import Path

import pytest

from agents.lock_manager import LockManager
from agents.obsidian_parser import read
from agents.pinterest_designer import PinterestDesigner
from agents.shared_models import Article, Offer


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


def _make_article() -> Article:
    return Article(
        id="article_001",
        offer_id="offer_test",
        title="Детская карта Альфа-Банк Условия",
        slug="detskaya-karta-alfa-bank-usloviya",
        status="draft",
        content="# Детская карта Альфа-Банк условия\n\nОбслуживание бесплатно при пополнении от 1000 рублей.\nКэшбэк до 5%.\n",
        markdown_path="",
        html_path="",
        word_count=15,
        requires_manual_verification=True,
        target_platforms=["blog"],
        utm_source="myfinq.xyz",
        meta_title="Детская карта Альфа-Банк условия",
        meta_description="Условия детской карты Альфа-Банк: кэшбэк, обслуживание, пополнение.",
    )


def test_design_creates_pin(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    article = _make_article()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    designer = PinterestDesigner(lock_manager=lm)
    pin = designer.design(article)

    assert pin.id.startswith("pin_")
    assert pin.article_id == article.id
    assert pin.title
    assert len(pin.title) <= 100
    assert pin.description
    assert len(pin.description) <= 500
    assert pin.image_prompt
    assert pin.status == "draft"
    assert pin.board == "myfinq_articles"


def test_pin_saved_in_obsidian(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    article = _make_article()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    designer = PinterestDesigner(lock_manager=lm)
    pin = designer.design(article)

    loaded = read("pin", pin.id)
    assert loaded.id == pin.id
    assert loaded.article_id == article.id
    assert loaded.title == pin.title
    assert loaded.description == pin.description
