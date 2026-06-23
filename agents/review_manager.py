from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from agents.lock_manager import LockManager
from agents.shared_models import LockFile


class ReviewStatusFile(BaseModel):
    entity_id: str
    entity_type: str
    status: str = Field(
        ...,
        pattern=r"^(pending|approved|rejected)$"
    )
    submitted_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    reviewed_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    source_path: Optional[str] = None
    output_path: Optional[str] = None


class ReviewManager:
    def __init__(
        self,
        review_root: str = "data/Review_Queue",
        exports_root: str = "data/Exports",
        lock_manager: Optional[LockManager] = None
    ):
        self.review_root = Path(review_root)
        self.exports_root = Path(exports_root)
        self.lock_manager = lock_manager or LockManager()
        self._ready_dir = self.exports_root / "Ready_To_Publish"
        self._ready_dir.mkdir(parents=True, exist_ok=True)

    def submit_for_review(
        self,
        entity_id: str,
        entity_type: str,
        source_path: Path
    ) -> ReviewStatusFile:
        folder = self._queue_folder(entity_type)
        folder.mkdir(parents=True, exist_ok=True)
        dest_file = folder / f"{entity_id}{source_path.suffix}"
        shutil.copy2(source_path, dest_file)
        status = ReviewStatusFile(
            entity_id=entity_id,
            entity_type=entity_type,
            status="pending",
            source_path=str(dest_file),
        )
        self._write_status(folder / f"{entity_id}.json", status)
        return status

    def approve(
        self,
        entity_id: str,
        entity_type: str
    ) -> ReviewStatusFile:
        folder = self._queue_folder(entity_type)
        status = self._read_status(folder / f"{entity_id}.json")
        lock_path = self.lock_manager._lock_path(entity_type, entity_id)
        acquired, msg = self.lock_manager.acquire_lock(
            entity_type, entity_id, "review_manager"
        )
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            status.status = "approved"
            status.reviewed_at = datetime.now(timezone.utc).isoformat()
            src = Path(status.source_path) if status.source_path else None
            if src and src.exists():
                dest = self._ready_dir / src.name
                shutil.move(str(src), str(dest))
                status.output_path = str(dest)
            self._write_status(folder / f"{entity_id}.json", status)
            return status
        finally:
            self.lock_manager.release_lock(entity_type, entity_id)

    def reject(
        self,
        entity_id: str,
        entity_type: str,
        reason: str = ""
    ) -> ReviewStatusFile:
        folder = self._queue_folder(entity_type)
        status = self._read_status(folder / f"{entity_id}.json")
        lock_path = self.lock_manager._lock_path(entity_type, entity_id)
        acquired, msg = self.lock_manager.acquire_lock(
            entity_type, entity_id, "review_manager"
        )
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            status.status = "rejected"
            status.reviewed_at = datetime.now(timezone.utc).isoformat()
            status.rejection_reason = reason or ""
            src = Path(status.source_path) if status.source_path else None
            if src and src.exists():
                src.unlink()
            self._write_status(folder / f"{entity_id}.json", status)
            return status
        finally:
            self.lock_manager.release_lock(entity_type, entity_id)

    def _queue_folder(self, entity_type: str) -> Path:
        mapping = {
            "article": "articles",
            "telegram_post": "telegram",
            "pin": "pinterest",
        }
        sub = mapping.get(entity_type, "articles")
        return self.review_root / sub

    def _status_path(self, entity_id: str) -> Path:
        return self.review_root / f"{entity_id}.json"

    def _write_status(self, path: Path, status: ReviewStatusFile) -> None:
        path.write_text(
            json.dumps(status.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _read_status(self, path: Path) -> ReviewStatusFile:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ReviewStatusFile(**data)
