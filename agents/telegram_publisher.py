from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field

from agents.lock_manager import LockManager
from agents.obsidian_parser import write
from agents.shared_models import Article, TelegramPost


class TelegramPublisher:
    def __init__(self, llm_client=None, lock_manager: Optional[LockManager] = None, base_url: str = "https://myfinq.xyz"):
        self.llm_client = llm_client
        self.lock_manager = lock_manager or LockManager()
        self.base_url = base_url.rstrip("/")

    def create_post(self, article: Article) -> TelegramPost:
        text, cta_url = self._generate_telegram_content(article)
        post = TelegramPost(
            id=f"tg_{uuid.uuid4().hex[:8]}",
            article_id=article.id,
            text=text[:4096],
            status="draft",
        )
        saved = self._save_post(post)
        return saved

    def _generate_telegram_content(self, article: Article):
        if self.llm_client is not None:
            prompt = self._build_prompt(article)
            raw = self.llm_client.generate(prompt)
            return self._parse_llm_response(raw, article)
        title = article.title or article.id
        text = (
            f"<b>{title}</b>\n\n"
            f"{article.meta_description or ''}\n\n"
            "В статье:\n"
            "✅ Что это такое и как работает\n"
            "✅ Ключевые условия и ограничения\n"
            "✅ Как оформить онлайн\n\n"
            f"Читать полностью: <a href=\"{self._build_cta_url(article)}\">myfinq.xyz</a>"
        )
        return text, self._build_cta_url(article)

    def _build_prompt(self, article: Article) -> str:
        return (
            "Напиши короткий пост для Telegram на русском языке на основе статьи.\n"
            f"Заголовок: {article.title}\n"
            f"Описание: {article.meta_description or article.content[:300]}\n"
            "Структура:\n"
            "1. Цепляющий заголовок (жирный шрифтом через <b>)\n"
            "2. 2-3 абзаца без воды\n"
            "3. Список из 3-4 пунктов с пользой\n"
            "4. CTA со ссылкой на статью\n"
            "Используй HTML-разметку Telegram. Добавь UTM-метки к ссылке.\n"
            "Ответь готовым текстом."
        )

    def _parse_llm_response(self, raw: str, article: Article):
        text = raw.strip()
        cta_url = self._build_cta_url(article)
        return text, cta_url

    def _build_cta_url(self, article: Article) -> str:
        url = f"{self.base_url}/articles/{article.slug or article.id}"
        sep = "?" if "?" not in url else "&"
        return f"{url}{sep}utm_source=telegram&utm_campaign=pinned"

    def _save_post(self, post: TelegramPost) -> TelegramPost:
        acquired, msg = self.lock_manager.acquire_lock("telegram_post", post.id, "telegram_publisher")
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            path = write(post, "telegram_post")
            post.obsidian_path = path
            return post
        finally:
            self.lock_manager.release_lock("telegram_post", post.id)
