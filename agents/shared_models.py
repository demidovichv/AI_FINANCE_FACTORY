from __future__ import annotations

import os
import uuid

from datetime import datetime, timedelta, date, timezone
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

    category: Optional[str] = None

    target_audience: Optional[str] = None

    key_terms: Optional[List[str]] = None

    description: Optional[str] = None

    status: str = Field(
        ...,
        pattern=r"^(active|draft|archived)$"
    )

    created_at: Optional[date] = None

    obsidian_path: Optional[str] = None


class Keyword(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^kw_[a-z0-9_]+$"
    )

    text: str

    search_volume: Optional[int] = None

    difficulty: Optional[int] = Field(
        None,
        ge=0,
        le=100
    )

    intent: Optional[str] = Field(
        None,
        pattern=r"^(informational|transactional|navigational|commercial)$"
    )

    cluster_id: Optional[str] = None

    created_at: Optional[date] = None

    obsidian_path: Optional[str] = None


class Cluster(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^cluster_[a-z0-9_]+$"
    )

    name: str

    pillar_keyword_id: Optional[str] = None

    related_keyword_ids: List[str] = Field(
        default_factory=list
    )

    created_at: Optional[date] = None

    obsidian_path: Optional[str] = None


class Article(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^article_[0-9]+$"
    )

    offer_id: str

    title: Optional[str] = None

    slug: Optional[str] = None

    status: str = Field(
        ...,
        pattern=r"^(draft|processing|review|published|fact_checking)$"
    )

    content: Optional[str] = None

    markdown_path: Optional[str] = None

    html_path: Optional[str] = None

    word_count: int = 0

    seo_score: Optional[float] = None

    requires_manual_verification: bool = False

    target_platforms: List[str] = Field(
        default_factory=lambda: ["blog"]
    )

    utm_source: Optional[str] = None

    meta_title: Optional[str] = None

    meta_description: Optional[str] = None

    fact_check_notes: List[str] = Field(
        default_factory=list
    )

    content_html: Optional[str] = None

    obsidian_path: Optional[str] = None


class Pin(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^pin_[a-z0-9_]+$"
    )

    article_id: str

    title: str

    description: str

    image_prompt: str

    board: str

    status: str = Field(
        ...,
        pattern=r"^(draft|ready|published|failed)$"
    )

    created_at: Optional[date] = None

    obsidian_path: Optional[str] = None


class TelegramPost(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^tg_[a-z0-9_]+$"
    )

    article_id: str

    text: str

    status: str = Field(
        ...,
        pattern=r"^(draft|ready|published|failed)$"
    )

    created_at: Optional[date] = None

    published_at: Optional[datetime] = None

    obsidian_path: Optional[str] = None


class EmailLetter(BaseModel):
    subject: str
    content: str
    delay_days: int = Field(default=0, ge=0)


class EmailSequence(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^email_[a-z0-9_]+$"
    )

    article_id: str

    sequence_name: str

    emails: List[EmailLetter] = Field(
        default_factory=list
    )

    status: str = Field(
        ...,
        pattern=r"^(draft|ready|published|failed)$"
    )

    created_at: Optional[date] = None

    obsidian_path: Optional[str] = None


class YouTubeScript(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^yt_[a-z0-9_]+$"
    )

    article_id: str

    title: str

    script_text: str

    thumbnail_prompt: Optional[str] = None

    tags: List[str] = Field(
        default_factory=list
    )

    status: str = Field(
        ...,
        pattern=r"^(draft|ready|published|failed)$"
    )

    created_at: Optional[date] = None

    obsidian_path: Optional[str] = None


class Report(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^report_[a-z0-9_]+$"
    )

    report_type: str = Field(
        ...,
        pattern=r"^(analytics|keyword|content|financial)$"
    )

    period: str

    data_path: Optional[str] = None

    created_at: Optional[date] = None

    obsidian_path: Optional[str] = None


# ---------- Pipeline ----------

class PipelineHistoryItem(BaseModel):
    stage: str

    status: str = Field(
        ...,
        pattern=r"^(success|failed|skipped)$"
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    message: Optional[str] = None


class PipelineState(BaseModel):
    entity_id: str

    entity_type: str = Field(
        ...,
        pattern=r"^(offer|keyword|cluster|article|pin|telegram_post|email_sequence|youtube_script|report)$"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
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
        pattern=r"^(offer|keyword|cluster|article|pin|telegram_post|email_sequence|youtube_script|report)$"
    )

    entity_id: str

    lock_id: str = Field(
        default_factory=lambda: (
            f"lock_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_"
            f"{str(uuid.uuid4())[:8]}"
        )
    )

    locked_by: str

    locked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
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
            datetime.now(timezone.utc) + timedelta(hours=2)
        )
    )
