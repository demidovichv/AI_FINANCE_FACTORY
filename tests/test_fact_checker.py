from pathlib import Path

import pytest

from agents.fact_checker import FactChecker
from agents.lock_manager import LockManager
from agents.obsidian_parser import read
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


def _make_offer() -> Offer:
    return Offer(
        id="offer_alfa_kids",
        name="Детская карта Альфа-Банк",
        bank="Альфа-Банк",
        offer_url="https://alfabank.ru/everyday/debit-cards/childcard/",
        affiliate_url="https://pxl.leads.su/click/143910aa13a118ff05bebb2b88465cfc",
        status="active",
        key_terms=["кэшбэк до 5%", "обслуживание бесплатно", "1000 рублей", "детская карта"],
        description="Детская карта с кэшбэком до 5%, бесплатное обслуживание при пополнении от 1000 рублей.",
    )


def _make_article(content: str) -> Article:
    return Article(
        id="article_001",
        offer_id="offer_alfa_kids",
        title="Детская карта Альфа-Банк Условия",
        slug="detskaya-karta-alfa-bank-usloviya",
        status="draft",
        content=content,
        requires_manual_verification=False,
    )


def test_fact_checker_marks_made_up_percentage(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    offer = _make_offer()
    article = _make_article(
        "# Детская карта Альфа-Банк условия\n\n"
        "Кэшбэк до 10% на все покупки.\n"
        "Обслуживание бесплатно.\n"
        "Карта оформляется онлайн за 5 минут.\n"
    )
    
    lm = LockManager(lock_dir=str(temp_lock_dir))
    checker = FactChecker(lock_manager=lm)
    checked = checker.check(article, offer)
    
    assert checked.status == "fact_checking"
    assert checked.requires_manual_verification is True
    assert any("10%" in note for note in checked.fact_check_notes)
    assert any("Requires Manual Verification" in note for note in checked.fact_check_notes)


def test_fact_checker_verifies_offer_data(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    offer = _make_offer()
    article = _make_article(
        "# Обзор карты\n\n"
        "Обслуживание бесплатно при пополнении от 1000 рублей.\n"
        "Кэшбэк до 5%.\n"
    )
    
    lm = LockManager(lock_dir=str(temp_lock_dir))
    checker = FactChecker(lock_manager=lm)
    checked = checker.check(article, offer)
    
    assert checked.status == "fact_checking"
    assert any("Verified against Offer" in note for note in checked.fact_check_notes)


def test_fact_checker_updates_article_file(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    offer = _make_offer()
    article = _make_article(
        "# Тест статьи\n\n"
        "Кэшбэк до 15% на все покупки.\n"
        "Обслуживание бесплатно.\n"
    )
    
    lm = LockManager(lock_dir=str(temp_lock_dir))
    checker = FactChecker(lock_manager=lm)
    checked = checker.check(article, offer)
    
    loaded = read("article", checked.id)
    assert loaded.status == "fact_checking"
    assert loaded.fact_check_notes == checked.fact_check_notes
