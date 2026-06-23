from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from agents import offer_loader
from agents.obsidian_parser import (
    Article,
    delete,
    exists,
    read,
    write,
)
from agents.shared_models import Article as ArticleModel, Offer, Keyword, Cluster


@pytest.fixture()
def temp_obsidian(tmp_path: Path) -> Path:
    root = tmp_path / "Obsidian"
    (root / "Articles" / "drafts").mkdir(parents=True)
    (root / "Articles" / "html").mkdir(parents=True)
    (root / "Offers").mkdir()
    return root


def _inject_paths(paths: dict[str, Path]) -> None:
    import agents.obsidian_parser as parser

    parser._OBSIDIAN_ROOT = paths["root"]


def test_read_offer(temp_obsidian: Path) -> None:
    _inject_paths({"root": temp_obsidian})
    offer = Offer(
        id="offer_test",
        name="Test Card",
        offer_url="https://example.com",
        status="active",
    )
    write(offer, "offer")
    loaded = read("offer", "offer_test")
    assert loaded.id == "offer_test"
    assert loaded.status == "active"


def test_write_article_to_drafts(temp_obsidian: Path) -> None:
    _inject_paths({"root": temp_obsidian})
    article = Article(
        id="article_001",
        offer_id="offer_test",
        status="draft",
        content="# Header\n\nBody.",
        requires_manual_verification=True,
    )
    path = write(article, "article")
    assert temp_obsidian.joinpath("Articles", "drafts", "article_001.md").exists()
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8").split("---", 2)[1])
    assert data["id"] == "article_001"
    assert data["requires_manual_verification"] is True
