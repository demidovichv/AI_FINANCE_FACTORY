from __future__ import annotations

import os
import uuid

from datetime import datetime, timedelta, date
from typing import Optional, List

from pydantic import BaseModel, Field


# ---------- Бизнес-сущности ----------

class Offer(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^offer_[a-z0-9_]+$"
    )

    name: str

    offer_url: str

    affiliate_url: Optional[str] = None

    bank: Optional[str] = None

    status: str = Field(
        ...,
        pattern=r"^(active|draft|archived)$"
    )

    created_at: Optional[date] = None


class Article(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^article_[0-9]+$"
    )

    offer_id: str

    status: str = Field(
        ...,
        pattern=r"^(draft|processing|review|published)$"
    )

    markdown_path: Optional[str] = None
    html_path: Optional[str] = None


# ---------- Pipeline ----------

class PipelineHistoryItem(BaseModel):
    stage: str

    status: str = Field(
        ...,
        pattern=r"^(success|failed|skipped)$"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )

    message: Optional[str] = None


class PipelineState(BaseModel):
    entity_id: str

    entity_type: str = Field(
        ...,
        pattern=r"^(offer|keyword|article|pin|report)$"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    current_stage: str = "init"

    status: str = Field(
        ...,
        pattern=r"^(pending|processing|success|failed|waiting_review)$"
    )

    parent_ids: List[str] = Field(
        default_factory=list
    )

    child_ids: List[str] = Field(
        default_factory=list
    )

    retry_count: int = 0

    max_retries: int = 4

    last_error: Optional[str] = None

    human_review_needed: bool = False

    history: List[PipelineHistoryItem] = Field(
        default_factory=list
    )


# ---------- Lock ----------

class LockFile(BaseModel):
    entity_type: str = Field(
        ...,
        pattern=r"^(offer|keyword|article|pin|report)$"
    )

    entity_id: str

    lock_id: str = Field(
        default_factory=lambda: (
            f"lock_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_"
            f"{str(uuid.uuid4())[:8]}"
        )
    )

    locked_by: str

    locked_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    hostname: str = Field(
        default_factory=lambda: os.getenv(
            "COMPUTERNAME",
            os.getenv("HOSTNAME", "unknown")
        )
    )

    pid: int = Field(
        default_factory=os.getpid
    )

    expires_at: datetime = Field(
        default_factory=lambda: (
            datetime.utcnow() + timedelta(hours=2)
        )
    )