from __future__ import annotations

import json

from datetime import datetime
from pathlib import Path

from agents.shared_models import LockFile


class LockManager:
    def __init__(self, lock_dir: str = ".locks"):
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def _lock_path(
        self,
        entity_type: str,
        entity_id: str
    ) -> Path:
        return self.lock_dir / f"{entity_id}.lock"

    def acquire_lock(
        self,
        entity_type: str,
        entity_id: str,
        locked_by: str
    ) -> tuple[bool, str]:

        lock_path = self._lock_path(
            entity_type,
            entity_id
        )

        if lock_path.exists():

            try:
                data = json.loads(
                    lock_path.read_text(
                        encoding="utf-8"
                    )
                )

                existing_lock = LockFile(
                    **data
                )

                if (
                    existing_lock.expires_at >
                    datetime.utcnow()
                ):
                    return (
                        False,
                        f"Lock already exists: {entity_id}"
                    )

                lock_path.unlink()

            except Exception:
                lock_path.unlink()

        lock = LockFile(
            entity_type=entity_type,
            entity_id=entity_id,
            locked_by=locked_by
        )

        lock_path.write_text(
            json.dumps(
                lock.model_dump(
                    mode="json"
                ),
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        return (
            True,
            f"Lock acquired: {entity_id}"
        )

    def release_lock(
        self,
        entity_type: str,
        entity_id: str
    ) -> bool:

        lock_path = self._lock_path(
            entity_type,
            entity_id
        )

        if lock_path.exists():
            lock_path.unlink()
            return True

        return False

    def cleanup_expired_locks(
        self
    ) -> int:

        removed = 0

        for lock_file in self.lock_dir.glob(
            "*.lock"
        ):
            try:

                data = json.loads(
                    lock_file.read_text(
                        encoding="utf-8"
                    )
                )

                lock = LockFile(
                    **data
                )

                if (
                    lock.expires_at <
                    datetime.utcnow()
                ):
                    lock_file.unlink()
                    removed += 1

            except Exception:
                lock_file.unlink()
                removed += 1

        return removed