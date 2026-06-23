from pathlib import Path

import pytest

from agents.html_renderer import HTMLRenderer
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


@pytest.fixture()
def temp_templates_dir(tmp_path: Path) -> Path:
    tpl_dir = tmp_path / "templates" / "html"
    tpl_dir.mkdir(parents=True)
    tpl_file = tpl_dir / "base.html"
    tpl_file.write_text(
        """<!DOCTYPE html>
<html lang="ru">
<head>
    <title>{{ title }}</title>
    <meta name="description" content="{{ meta_description }}">
</head>
<body>
    <article>
        <h1>{{ title }}</h1>
        <div class="content">{{ content | safe }}</div>
        {% if cta_button %}
        <a href="{{ cta_button.href }}">{{ cta_button.text }}</a>
        {% endif %}
    </article>
</body>
</html>""",
        encoding="utf-8",
    )
    return tpl_dir


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


def _make_offer() -> Offer:
    return Offer(
        id="offer_test",
        name="Детская карта Альфа-Банк",
        bank="Альфа-Банк",
        offer_url="https://example.com",
        affiliate_url="https://example.com/affiliate",
        status="active",
    )


def test_render_creates_html_file(
    temp_obsidian: Path,
    temp_lock_dir: Path,
    temp_templates_dir: Path,
) -> None:
    article = _make_article()
    offer = _make_offer()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    renderer = HTMLRenderer(lock_manager=lm)
    path = renderer.render(article, offer)
    
    assert Path(path).exists()
    html_text = Path(path).read_text(encoding="utf-8")
    assert "<h1>" in html_text
    assert "<p>" in html_text
    assert "affiliate" in html_text
    assert article.content_html is not None
    assert article.status == "rendered"


def test_render_updates_article_model(
    temp_obsidian: Path,
    temp_lock_dir: Path,
    temp_templates_dir: Path,
) -> None:
    article = _make_article()
    offer = _make_offer()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    renderer = HTMLRenderer(lock_manager=lm)
    path = renderer.render(article, offer)
    
    assert article.content_html is not None
    assert article.status == "rendered"
    assert article.html_path == path


def test_render_without_offer(
    temp_obsidian: Path,
    temp_lock_dir: Path,
    temp_templates_dir: Path,
) -> None:
    article = _make_article()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    renderer = HTMLRenderer(lock_manager=lm)
    path = renderer.render(article)
    
    assert Path(path).exists()
    html_text = Path(path).read_text(encoding="utf-8")
    assert "<h1>" in html_text
    assert article.status == "rendered"
