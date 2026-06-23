from pathlib import Path

import pytest

from agents.article_generator import ArticleGenerator
from agents.idempotency import IdempotencyManager
from agents.lock_manager import LockManager
from agents.obsidian_parser import read
from agents.shared_models import Cluster, Keyword, Offer


@pytest.fixture()
def temp_obsidian(tmp_path: Path) -> Path:
    root = tmp_path / "Obsidian"
    (root / "Keywords").mkdir(parents=True)
    (root / "Clusters").mkdir()
    (root / "Articles" / "drafts").mkdir(parents=True)
    (root / "Articles" / "html").mkdir(parents=True)
    (root / "Pins").mkdir()
    (root / "Telegram").mkdir()
    (root / "YouTube").mkdir()
    (root / "Email").mkdir()
    (root / "Offers").mkdir()
    (root / "Reports").mkdir()
    import agents.obsidian_parser as parser
    parser._OBSIDIAN_ROOT = root
    return root


@pytest.fixture()
def temp_lock_dir(tmp_path: Path) -> Path:
    return tmp_path / ".locks"


@pytest.fixture()
def temp_pipeline_dir(tmp_path: Path) -> Path:
    return tmp_path / "Pipeline_Status"


def _make_offer(offer_id: str = "offer_test") -> Offer:
    return Offer(
        id=offer_id,
        name="Детская карта Альфа-Банк",
        bank="Альфа-Банк",
        offer_url="https://example.com",
        status="active",
    )


def _make_keyword(kw_id: str = "kw_1") -> Keyword:
    return Keyword(
        id=kw_id,
        text="детская карта Альфа-Банк условия",
        intent="informational",
        search_volume=1000,
        difficulty=30,
    )


def test_generate_article_creates_file(
    temp_obsidian: Path,
    temp_lock_dir: Path,
    temp_pipeline_dir: Path
) -> None:
    offer = _make_offer()
    keyword = _make_keyword()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    idempotency = IdempotencyManager(pipeline_dir=str(temp_pipeline_dir))
    generator = ArticleGenerator(lock_manager=lm, idempotency=idempotency)
    article = generator.generate(offer, keyword)

    assert article.id.startswith("article_")
    assert article.title == keyword.text.title()
    assert article.slug
    assert article.content
    assert article.requires_manual_verification is True
    assert article.status == "draft"
    assert article.target_platforms == ["blog"]
    assert article.utm_source == "myfinq.xyz"
    assert article.meta_title == keyword.text

    loaded = read("article", article.id)
    assert loaded.id == article.id
    assert loaded.title == article.title


def test_generate_is_idempotent(
    temp_obsidian: Path,
    temp_lock_dir: Path,
    temp_pipeline_dir: Path
) -> None:
    offer = _make_offer()
    keyword = _make_keyword()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    idempotency = IdempotencyManager(pipeline_dir=str(temp_pipeline_dir))
    generator = ArticleGenerator(lock_manager=lm, idempotency=idempotency)
    article1 = generator.generate(offer, keyword)
    article2 = generator.generate(offer, keyword)

    assert article1.id == article2.id
    assert article1.title == article2.title
    assert article1.content == article2.content


def test_generate_with_cluster(
    temp_obsidian: Path,
    temp_lock_dir: Path,
    temp_pipeline_dir: Path
) -> None:
    offer = _make_offer()
    keyword = _make_keyword()
    cluster = Cluster(
        id="cluster_001",
        name="Детские карты",
        pillar_keyword_id=keyword.id,
        related_keyword_ids=[],
    )
    lm = LockManager(lock_dir=str(temp_lock_dir))
    idempotency = IdempotencyManager(pipeline_dir=str(temp_pipeline_dir))
    generator = ArticleGenerator(lock_manager=lm, idempotency=idempotency)
    article = generator.generate(offer, keyword, cluster)

    assert article.id.startswith("article_")
    assert article.content
