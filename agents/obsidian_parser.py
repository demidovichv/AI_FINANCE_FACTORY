from __future__ import annotations

import shutil
from pathlib import Path
from typing import Type, TypeVar

import yaml

from pydantic import BaseModel

from agents.shared_models import (
    Article,
    Cluster,
    EmailSequence,
    Keyword,
    Offer,
    Pin,
    Report,
    TelegramPost,
    YouTubeScript,
)


T = TypeVar("T", bound=BaseModel)

_OBSIDIAN_ROOT = Path(__file__).resolve().parent.parent / "Obsidian"

_ENTITY_MAP: dict[str, Type[BaseModel]] = {
    "offer": Offer,
    "keyword": Keyword,
    "cluster": Cluster,
    "article": Article,
    "pin": Pin,
    "telegram_post": TelegramPost,
    "email_sequence": EmailSequence,
    "youtube_script": YouTubeScript,
    "report": Report,
}


def _entity_dir(entity_type: str) -> Path:
    folder = {
        "offer": "Offers",
        "keyword": "Keywords",
        "cluster": "Clusters",
        "article": "Articles",
        "pin": "Pins",
        "telegram_post": "Telegram",
        "email_sequence": "Email",
        "youtube_script": "YouTube",
        "report": "Reports",
    }.get(entity_type)

    if folder is None:
        raise ValueError(f"Неизвестный тип сущности: {entity_type}")

    return _OBSIDIAN_ROOT / folder


def _to_model(entity_type: str, data: dict) -> BaseModel:
    model = _ENTITY_MAP.get(entity_type)
    if model is None:
        raise ValueError(f"Нет модели для типа: {entity_type}")
    return model(**data)


def _fallback_body(text: str) -> str:
    lines = text.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if body_start == 0:
                body_start = i + 1
            else:
                body_start = i + 1
                break
    return "\n".join(lines[body_start:]).strip()


def read(entity_type: str, entity_id: str) -> BaseModel:
    folder = _entity_dir(entity_type)
    candidates = [folder / f"{entity_id}.md"]
    if entity_type == "article":
        candidates += [
            folder / "drafts" / f"{entity_id}.md",
            folder / "html" / f"{entity_id}.md",
        ]
    target = None
    for path in candidates:
        if path.exists():
            target = path
            break
    if target is None:
        raise FileNotFoundError(
            f"Файл сущности не найден: {entity_id}.md в {folder}"
        )
    raw = target.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Некорректный формат Obsidian-файла: отсутствует YAML-шапка.")
    data = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip() if len(parts) > 2 else ""
    if entity_type == "article":
        data.setdefault("content", body)
    data.setdefault("obsidian_path", str(target))
    return _to_model(entity_type, data)


def write(entity: BaseModel, entity_type: str | None = None) -> str:
    if entity_type is None:
        entity_type = _detect_type(entity)
    folder = _entity_dir(entity_type)
    folder.mkdir(parents=True, exist_ok=True)
    entity_id = getattr(entity, "id", None)
    if not entity_id:
        raise ValueError("У сущности отсутствует поле id")
    entity_dict = entity.model_dump()
    body_text = ""
    if entity_type == "article":
        body_text = entity_dict.pop("content", "") or ""
    entity_dict.pop("obsidian_path", None)
    target = folder / f"{entity_id}.md"
    if entity_type == "article":
        target = folder / "drafts" / f"{entity_id}.md"
    yaml_block = yaml.safe_dump(
        entity_dict, allow_unicode=True, sort_keys=False
    ).strip()
    markdown = f"---\n{yaml_block}\n---\n\n{body_text}\n"
    target.write_text(markdown, encoding="utf-8")
    return str(target)


def _detect_type(entity: BaseModel) -> str:
    for key, model in _ENTITY_MAP.items():
        if isinstance(entity, model):
            return key
    raise ValueError(f"Неизвестный тип сущности: {type(entity)}")


def exists(entity_type: str, entity_id: str) -> bool:
    folder = _entity_dir(entity_type)
    candidates = [folder / f"{entity_id}.md"]
    if entity_type == "article":
        candidates += [
            folder / "drafts" / f"{entity_id}.md",
            folder / "html" / f"{entity_id}.md",
        ]
    return any(path.exists() for path in candidates)


def delete(entity_type: str, entity_id: str) -> None:
    folder = _entity_dir(entity_type)
    candidates = [folder / f"{entity_id}.md"]
    if entity_type == "article":
        candidates += [
            folder / "drafts" / f"{entity_id}.md",
            folder / "html" / f"{entity_id}.md",
        ]
    removed = False
    for path in candidates:
        if path.exists():
            path.unlink()
            removed = True
    if not removed:
        raise FileNotFoundError(
            f"Файл сущности не найден для удаления: {entity_id}.md в {folder}"
        )
