from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from agents.idempotency import IdempotencyManager
from agents.knowledge_memory_agent import KnowledgeMemoryAgent
from agents.lock_manager import LockManager
from agents.obsidian_parser import exists, read, write
from agents.shared_models import Article, Cluster, Keyword, Offer


class ArticleGenerator:
    def __init__(
        self,
        llm_client=None,
        lock_manager: Optional[LockManager] = None,
        idempotency: Optional[IdempotencyManager] = None,
        memory: Optional[KnowledgeMemoryAgent] = None
    ):
        self.llm_client = llm_client
        self.lock_manager = lock_manager or LockManager()
        self.idempotency = idempotency or IdempotencyManager()
        self.memory = memory or KnowledgeMemoryAgent()

    def generate(
        self,
        offer: Offer,
        keyword: Keyword,
        cluster: Optional[Cluster] = None
    ) -> Article:
        uniqueness = self.memory.check_uniqueness(keyword.text)
        if uniqueness["status"] == "duplicate":
            import logging
            logging.getLogger(__name__).warning(
                "Uniqueness check: %s", uniqueness["message"]
            )
        
        if self.idempotency.article_exists(offer.id):
            existing = self._find_existing_article(offer, keyword)
            if existing:
                return existing

        if self._article_exists_in_obsidian(offer, keyword):
            return self._load_existing_article(offer, keyword)

        content = self._generate_content(offer, keyword, cluster)
        article_id = self._generate_article_id()

        article = Article(
            id=article_id,
            offer_id=offer.id,
            title=keyword.text.title(),
            slug=self._slugify(keyword.text),
            content=content,
            status="draft",
            word_count=len(content.split()),
            requires_manual_verification=True,
            markdown_path="",
            html_path="",
            seo_score=None,
            target_platforms=["blog"],
            utm_source="myfinq.xyz",
            meta_title=keyword.text,
            meta_description=content.split("\n")[0][:160],
        )

        acquired, msg = self.lock_manager.acquire_lock(
            "article", article_id, "article_generator"
        )
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            path = write(article, "article")
            article.obsidian_path = path
            article.markdown_path = path
            return article
        finally:
            self.lock_manager.release_lock("article", article_id)

    def _build_prompt(
        self,
        offer: Offer,
        keyword: Keyword,
        cluster: Optional[Cluster]
    ) -> str:
        return (
            "Напиши SEO-статью на русском языке для блога myfinq.xyz.\n"
            f"Оффер: {offer.name}\n"
            f"Банк: {offer.bank or 'Не указан'}\n"
            f"Ключевое слово: {keyword.text}\n"
            f"Интент: {keyword.intent or 'informational'}\n"
            f"Кластер: {cluster.name if cluster else 'Не указан'}\n"
            "Структура: H1 с ключевым словом, 3-5 секций H2, "
            "введение, заключение с CTA.\n"
            "Тон: экспертный, дружелюбный, без агрессивных продаж.\n"
            "Верни готовый Markdown-текст."
        )

    def _generate_content(
        self,
        offer: Offer,
        keyword: Keyword,
        cluster: Optional[Cluster]
    ) -> str:
        if self.llm_client is not None:
            prompt = self._build_prompt(offer, keyword, cluster)
            raw = self.llm_client.generate(prompt)
            return self._parse_llm_response(raw)
        return self._mock_content(offer, keyword)

    def _parse_llm_response(self, raw: str) -> str:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```\w*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        return cleaned.strip()

    def _mock_content(self, offer: Offer, keyword: Keyword) -> str:
        title = keyword.text.title()
        intro = (
            f"В этой статье мы подробно разберем, что такое "
            f"{keyword.text.lower()}, как это работает и почему это важно для вас."
        )
        sections = [
            f"## Что такое {keyword.text.lower()}?",
            f"## Как работает {keyword.text.lower()}",
            "## Преимущества и особенности",
            f"## Как оформить {keyword.text.lower()}",
            "## Часто задаваемые вопросы",
        ]
        body = "\n\n".join(
            [
                f"# {title}",
                intro,
                *sections,
                "---",
                (
                    "> ⚠️ **Важно:** все цифры и условия "
                    "требуют ручной проверки перед публикацией."
                ),
            ]
        )
        return body

    def _slugify(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_]+", "-", text)
        return text.strip("-")[:50]

    def _find_existing_article(
        self,
        offer: Offer,
        keyword: Keyword
    ) -> Optional[Article]:
        if not self._article_exists_in_obsidian(offer, keyword):
            return None
        return self._load_existing_article(offer, keyword)

    def _article_exists_in_obsidian(
        self,
        offer: Offer,
        keyword: Keyword
    ) -> bool:
        articles_dir = self._obsidian_articles_dir()
        if not articles_dir.exists():
            return False
        title = keyword.text.title()
        for path in articles_dir.glob("article_*.md"):
            try:
                art = read("article", path.stem)
                if art.offer_id == offer.id and art.title == title:
                    return True
            except Exception:
                continue
        return False

    def _load_existing_article(
        self,
        offer: Offer,
        keyword: Keyword
    ) -> Article:
        articles_dir = self._obsidian_articles_dir()
        title = keyword.text.title()
        for path in articles_dir.glob("article_*.md"):
            try:
                art = read("article", path.stem)
                if art.offer_id == offer.id and art.title == title:
                    return art
            except Exception:
                continue
        raise RuntimeError("Не удалось загрузить существующую статью")

    def _obsidian_articles_dir(self) -> Path:
        import agents.obsidian_parser as parser
        return parser._OBSIDIAN_ROOT / "Articles" / "drafts"

    def _generate_article_id(self) -> str:
        articles_dir = self._obsidian_articles_dir()
        if not articles_dir.exists():
            return "article_001"
        max_num = 0
        for path in articles_dir.glob("article_*.md"):
            try:
                num = int(path.stem.split("_")[1])
                if num > max_num:
                    max_num = num
            except (IndexError, ValueError):
                continue
        return f"article_{max_num + 1:03d}"
