from pathlib import Path

import pytest

from agents.email_sequence_generator import EmailSequenceGenerator
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


def test_generate_sequence_returns_email_sequence(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    article = _make_article()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    generator = EmailSequenceGenerator(lock_manager=lm)
    sequence = generator.generate_sequence(article)

    assert sequence.id.startswith("email_")
    assert sequence.article_id == article.id
    assert len(sequence.emails) >= 3
    assert sequence.status == "draft"

    for letter in sequence.emails:
        assert letter.subject
        assert letter.content
        assert letter.delay_days >= 0


def test_sequence_saved_in_obsidian(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    article = _make_article()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    generator = EmailSequenceGenerator(lock_manager=lm)
    sequence = generator.generate_sequence(article)

    loaded = read("email_sequence", sequence.id)
    assert loaded.id == sequence.id
    assert loaded.article_id == article.id
    assert len(loaded.emails) == len(sequence.emails)


def test_sequence_contains_utm_links(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    article = _make_article()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    generator = EmailSequenceGenerator(lock_manager=lm)
    sequence = generator.generate_sequence(article)

    assert any("utm_source=email" in letter.content for letter in sequence.emails)
    assert any(article.slug in letter.content or article.id in letter.content for letter in sequence.emails)
