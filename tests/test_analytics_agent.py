from pathlib import Path
import csv

import pytest

from agents.analytics_agent import AnalyticsAgent
from agents.lock_manager import LockManager
from agents.obsidian_parser import read
from agents.shared_models import Report


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
def temp_roots(tmp_path: Path):
    exports = tmp_path / "Exports"
    exports.mkdir(parents=True)
    return exports, tmp_path


def _write_metrics(path: Path, rows: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["entity_id", "entity_type", "views", "clicks", "saves", "avg_time_sec"])
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(zip(writer.fieldnames, row)))


def test_generate_report_creates_file(temp_obsidian, temp_roots):
    exports, tmp_path = temp_roots
    rows = [
        ["article_001", "article", 1000, 200, 50, 120.5],
        ["article_002", "article", 500, 80, 20, 60.0],
        ["article_003", "article", 2000, 400, 100, 180.2],
        ["pin_001", "pin", 3000, 150, 400, 0.0],
    ]
    _write_metrics(exports / "metrics_2024_06.csv", rows)
    agent = AnalyticsAgent(
        lock_manager=LockManager(lock_dir=str(tmp_path / ".locks")),
        metrics_dir=str(exports),
    )
    metrics = agent.collect_metrics()
    assert len(metrics) == 4
    report = agent.generate_report(metrics)
    assert report.id.startswith("report_")
    assert report.report_type == "analytics"
    assert Path(report.data_path).exists()
    text = Path(report.data_path).read_text(encoding="utf-8")
    assert "Top Performing Content" in text
    assert "Recommendations" in text
    assert "article_003" in text
    loaded = read("report", report.id)
    assert loaded.id == report.id
