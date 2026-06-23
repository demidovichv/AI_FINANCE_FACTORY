from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field

from agents.lock_manager import LockManager
from agents.obsidian_parser import write
from agents.shared_models import Article, Pin


class PinterestDesigner:
    def __init__(self, llm_client=None, lock_manager: Optional[LockManager] = None):
        self.llm_client = llm_client
        self.lock_manager = lock_manager or LockManager()

    def design(self, article: Article) -> Pin:
        title, description, tags, image_prompt = self._generate_pin_content(article)
        pin = Pin(
            id=f"pin_{uuid.uuid4().hex[:8]}",
            article_id=article.id,
            title=title[:100],
            description=description[:500],
            image_prompt=image_prompt,
            board="myfinq_articles",
            status="draft",
        )
        saved = self._save_pin(pin)
        return saved

    def _generate_pin_content(self, article: Article):
        if self.llm_client is not None:
            prompt = self._build_prompt(article)
            raw = self.llm_client.generate(prompt)
            return self._parse_llm_response(raw, article)
        
        base = article.title or article.id
        title = f"{base} — главные условия и преимущества"
        description = (
            f"В этой статье раскрываем тему «{article.title}». "
            "Обзор ключевых условий, сравнение предложений и рекомендации."
        )
        tags = [
            article.slug or article.id,
            "финансы",
            "личные_финансы",
            "инвестиции",
            "кэшбэк",
            "банк",
            "экономия",
            "советы",
            "мотивация",
            "рост",
            "успех",
        ][:15]
        image_prompt = (
            "infographic about personal finance topic, bright colors, "
            "minimalist style, clean layout, modern illustration, "
            "friendly tone, no text on image"
        )
        return title, description, tags, image_prompt

    def _build_prompt(self, article: Article) -> str:
        return (
            "Создай метаданные для Pinterest-пина на основе статьи.\n"
            f"Заголовок статьи: {article.title}\n"
            f"Описание: {article.meta_description or article.content[:200]}\n"
            "Сгенерируй:\n"
            "1. title — до 100 символов, привлекательный, с ключевым словом\n"
            "2. description — до 500 символов, с хэштегами и призывом\n"
            "3. tags — список 10-15 тегов через запятую\n"
            "4. image_prompt — промпт на английском для генерации обложки\n"
            "Ответ в формате JSON: {title, description, tags[], image_prompt}"
        )

    def _parse_llm_response(self, raw: str, article: Article):
        import json, re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return self._fallback(article)
        try:
            data = json.loads(match.group())
            title = data.get("title", article.title)[:100]
            description = data.get("description", article.meta_description or article.content or "")[:500]
            tags = data.get("tags", [])[:15]
            image_prompt = data.get("image_prompt", "")
            return title, description, tags, image_prompt
        except Exception:
            return self._fallback(article)

    def _fallback(self, article: Article):
        title = f"{article.title or article.id} — полезные советы"[:100]
        description = (article.meta_description or article.content or "")[:500]
        tags = [article.slug or article.id, "финансы", "советы", "экономия"][:15]
        image_prompt = (
            "informational image about finance topic, clean style, "
            "soft colors, minimal text, modern flat design"
        )
        return title, description, tags, image_prompt

    def _save_pin(self, pin: Pin) -> Pin:
        acquired, msg = self.lock_manager.acquire_lock("pin", pin.id, "pinterest_designer")
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            path = write(pin, "pin")
            pin.obsidian_path = path
            return pin
        finally:
            self.lock_manager.release_lock("pin", pin.id)
