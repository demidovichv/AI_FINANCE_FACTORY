from pathlib import Path

from agents.idempotency import (
    IdempotencyManager
)


def test_article_exists():

    test_dir = Path(
        "test_pipeline_status"
    )

    test_dir.mkdir(
        exist_ok=True
    )

    sample = test_dir / "article_001.json"

    sample.write_text(
        '{"offer_id":"offer_test"}',
        encoding="utf-8"
    )

    manager = IdempotencyManager(
        pipeline_dir=str(test_dir)
    )

    assert (
        manager.article_exists(
            "offer_test"
        )
        is True
    )