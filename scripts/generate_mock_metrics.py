"""
Генерация фейковых метрик для существующих статей и пинов.
Используется для тестирования AnalyticsAgent при отсутствии реальных данных.
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timezone
from pathlib import Path

RANDOM = random.Random(42)

EXPORT_DIR = Path("data/Exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

METRIC_ROWS = [
    ("article_001", "article", 1200, 350, 90, 145.0),
    ("article_002", "article", 800, 210, 45, 95.5),
    ("article_003", "article", 2100, 480, 130, 190.2),
    ("article_004", "article", 500, 120, 25, 60.0),
    ("article_005", "article", 1600, 400, 110, 155.5),
    ("article_006", "article", 300, 60, 10, 35.0),
    ("article_007", "article", 950, 230, 55, 110.0),
    ("pin_001", "pin", 3400, 180, 420, 0.0),
    ("pin_002", "pin", 2800, 150, 350, 0.0),
    ("pin_003", "pin", 1500, 90, 200, 0.0),
]


def generate() -> None:
    now = datetime.now(timezone.utc)
    filename = EXPORT_DIR / f"metrics_{now.strftime('%Y_%m')}.csv"
    with filename.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["entity_id", "entity_type", "views", "clicks", "saves", "avg_time_sec"])
        for entity_id, entity_type, views, clicks, saves, avg_time in METRIC_ROWS:
            writer.writerow([
                entity_id,
                entity_type,
                views,
                clicks,
                saves,
                avg_time,
            ])
    print(f"Generated {filename}")


if __name__ == "__main__":
    generate()
