from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from agents.lock_manager import LockManager
from agents.obsidian_parser import write
from agents.shared_models import Article, YouTubeScript


class YouTubeScriptGenerator:
    def __init__(self, llm_client=None, lock_manager: Optional[LockManager] = None):
        self.llm_client = llm_client
        self.lock_manager = lock_manager or LockManager()

    def generate_script(self, article: Article) -> YouTubeScript:
        script_text, thumbnail_prompt, tags = self._build_script_content(article)
        script = YouTubeScript(
            id=f"yt_{uuid.uuid4().hex[:8]}",
            article_id=article.id,
            title=article.title or article.id,
            script_text=script_text,
            thumbnail_prompt=thumbnail_prompt,
            tags=tags,
            status="draft",
        )
        saved = self._save_script(script)
        return saved

    def _build_script_content(self, article: Article):
        if self.llm_client is not None:
            prompt = self._build_prompt(article)
            raw = self.llm_client.generate(prompt)
            return self._parse_llm_response(raw, article)
        title = article.title or article.id
        script_text = (
            f"# {title}\n\n"
            "## Hook (0:00 - 0:05)\n"
            f"Привет! Сегодня разберем, что такое {title.lower()}, и почему это важно для ваших финансов.\n\n"
            "## Intro (0:05 - 0:20)\n"
            "В этом видео мы простым языком объясним ключевые моменты, условия и подводные камни.\n\n"
            "## Main Content (0:20 - 2:30)\n"
            "1. Суть продукта\n"
            "2. Ключевые условия\n"
            "3. Кому подходит\n"
            f"{article.content or ''}\n\n"
            "## CTA (2:30 - 2:40)\n"
            "Подпишитесь на канал и переходите по ссылке в описании для полной статьи на myfinq.xyz.\n"
        )
        thumbnail_prompt = (
            "YouTube thumbnail about personal finance, bold text, "
            "bright colors, clean design, professional look, "
            "no faces, minimal text, high contrast"
        )
        tags = [
            article.slug or article.id,
            "финансы",
            "личные_финансы",
            "банк",
            "советы",
            "экономия",
            "инвестиции",
            "деньги",
            "кэшбэк",
            "обзор",
            "урок",
        ][:15]
        return script_text, thumbnail_prompt, tags

    def _build_prompt(self, article: Article) -> str:
        return (
            "Напиши сценарий для YouTube-видео на русском языке на основе статьи.\n"
            f"Заголовок: {article.title}\n"
            f"Описание: {article.meta_description or article.content[:300]}\n"
            "Структура:\n"
            "1. Hook (цепляющее начало, первые 5 секунд)\n"
            "2. Intro (краткое представление)\n"
            "3. Main Content (основная часть, 3-4 блока)\n"
            "4. CTA (призыв подписаться и перейти по ссылке)\n"
            "Также добавь:\n"
            "- thumbnail_prompt — промпт на английском для обложки видео\n"
            "- tags — список 10-15 тегов\n"
            "Ответ в формате JSON: {script_text, thumbnail_prompt, tags[]}"
        )

    def _parse_llm_response(self, raw: str, article: Article):
        import json, re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return self._fallback(article)
        try:
            data = json.loads(match.group())
            script_text = data.get("script_text", "") or ""
            thumbnail_prompt = data.get("thumbnail_prompt", "")
            tags = data.get("tags", [])[:15]
            return script_text, thumbnail_prompt, tags
        except Exception:
            return self._fallback(article)

    def _fallback(self, article: Article):
        title = article.title or article.id
        script_text = (
            f"# {title}\n\n"
            "## Hook\nПривет! Сегодня разберем важную финансовую тему.\n\n"
            "## Intro\nВ этом видео мы объясним ключевые моменты простым языком.\n\n"
            "## Main Content\n"
            f"{article.content or 'Основная часть сценария.'}"
            "\n\n## CTA\nПодпишитесь и переходите по ссылке в описании."
        )
        thumbnail_prompt = (
            "YouTube thumbnail about finance, bold text, bright colors, clean design"
        )
        tags = [article.slug or article.id, "финансы", "советы", "экономия", "банк"][:15]
        return script_text, thumbnail_prompt, tags

    def _save_script(self, script: YouTubeScript) -> YouTubeScript:
        acquired, msg = self.lock_manager.acquire_lock("youtube_script", script.id, "youtube_script_generator")
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            path = write(script, "youtube_script")
            script.obsidian_path = path
            return script
        finally:
            self.lock_manager.release_lock("youtube_script", script.id)
