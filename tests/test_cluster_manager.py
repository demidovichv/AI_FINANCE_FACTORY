from pathlib import Path

import pytest

from agents.cluster_manager import ClusterManager
from agents.lock_manager import LockManager
from agents.obsidian_parser import read
from agents.shared_models import Keyword


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


def _make_keyword(kw_id: str, text: str, intent: str, volume: int = 1000, difficulty: int = 30) -> Keyword:
    return Keyword(
        id=kw_id,
        text=text,
        intent=intent,
        search_volume=volume,
        difficulty=difficulty,
    )


def test_build_clusters_groups_keywords(temp_obsidian: Path, temp_lock_dir: Path) -> None:
    keywords = [
        _make_keyword("kw_1", "детская карта Альфа-Банк отзыв", "informational", 1000),
        _make_keyword("kw_2", "детские карты для подростков", "informational", 800),
        _make_keyword("kw_3", "оформить детскую карту онлайн", "transactional", 600),
        _make_keyword("kw_4", "кэшбэк карта какой банк лучше", "commercial", 1200),
        _make_keyword("kw_5", "как работает кэшбэк", "informational", 900),
        _make_keyword("kw_6", "накопительный счет проценты", "informational", 700),
        _make_keyword("kw_7", "вклад с высоким процентом", "transactional", 500),
    ]
    lm = LockManager(lock_dir=str(temp_lock_dir))
    manager = ClusterManager(lock_manager=lm)
    clusters = manager.build_clusters(keywords)
    assert len(clusters) >= 2
    for cluster in clusters:
        assert cluster.id.startswith("cluster_")
        assert cluster.name
        assert isinstance(cluster.related_keyword_ids, list)


def test_saved_clusters_exist_in_obsidian(temp_obsidian: Path, temp_lock_dir: Path) -> None:
    keywords = [
        _make_keyword("kw_1", "детская карта отзыв", "informational", 1000),
        _make_keyword("kw_2", "детская карта условия", "informational", 800),
        _make_keyword("kw_3", "оформить детскую карту", "transactional", 500),
    ]
    lm = LockManager(lock_dir=str(temp_lock_dir))
    manager = ClusterManager(lock_manager=lm)
    clusters = manager.build_clusters(keywords)
    assert len(clusters) >= 1
    for cluster in clusters:
        loaded = read("cluster", cluster.id)
        assert loaded.id == cluster.id
        assert loaded.name == cluster.name
        assert loaded.pillar_keyword_id == cluster.pillar_keyword_id
        assert set(loaded.related_keyword_ids) == set(cluster.related_keyword_ids)


def test_pillar_is_highest_volume_keyword(temp_obsidian: Path, temp_lock_dir: Path) -> None:
    keywords = [
        _make_keyword("kw_low", "детская карта условия", "informational", 400),
        _make_keyword("kw_high", "детская карта отзыв", "informational", 1500),
        _make_keyword("kw_mid", "оформить детскую карту", "transactional", 700),
    ]
    lm = LockManager(lock_dir=str(temp_lock_dir))
    manager = ClusterManager(lock_manager=lm)
    clusters = manager.build_clusters(keywords)
    assert len(clusters) >= 1
    cluster = clusters[0]
    assert cluster.pillar_keyword_id == "kw_high"
