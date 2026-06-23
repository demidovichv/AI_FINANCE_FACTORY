from pathlib import Path

import pytest

from agents.lock_manager import LockManager
from agents.obsidian_parser import read
from agents.shared_models import Article, Offer
from agents.youtube_script_generator import YouTubeScriptGenerator


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


def test_generate_script_returns_youtube_script(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    article = _make_article()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    generator = YouTubeScriptGenerator(lock_manager=lm)
    script = generator.generate_script(article)

    assert script.id.startswith("yt_")
    assert script.article_id == article.id
    assert script.script_text
    assert script.thumbnail_prompt
    assert script.status == "draft"


def test_script_saved_in_obsidian(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    article = _make_article()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    generator = YouTubeScriptGenerator(lock_manager=lm)
    script = generator.generate_script(article)

    loaded = read("youtube_script", script.id)
    assert loaded.id == script.id
    assert loaded.article_id == article.id
    assert loaded.script_text == script.script_text


def test_script_has_required_sections(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    article = _make_article()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    generator = YouTubeScriptGenerator(lock_manager=lm)
    script = generator.generate_script(article)

    assert "Hook" in script.script_text or "hook" in script.script_text.lower()
    assert "Intro" in script.script_text or "intro" in script.script_text.lower()
    assert "CTA" in script.script_text or "cta" in script.script_text.lower()
    assert script.thumbnail_prompt
