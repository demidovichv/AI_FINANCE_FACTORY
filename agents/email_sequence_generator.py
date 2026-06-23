from __future__ import annotations

import json
import re
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from agents.lock_manager import LockManager
from agents.obsidian_parser import write
from agents.shared_models import Article, EmailSequence, EmailLetter


class EmailSequenceGenerator:
    def __init__(self, llm_client=None, lock_manager: Optional[LockManager] = None, base_url: str = "https://myfinq.xyz"):
        self.llm_client = llm_client
        self.lock_manager = lock_manager or LockManager()
        self.base_url = base_url.rstrip("/")

    def generate_sequence(self, article: Article) -> EmailSequence:
        sequence_name = f"Sequence: {article.title or article.id}"
        emails_data = self._build_email_content(article)
        emails = [
            EmailLetter(**letter_data) for letter_data in emails_data
        ]
        sequence = EmailSequence(
            id=f"email_{uuid.uuid4().hex[:8]}",
            article_id=article.id,
            sequence_name=sequence_name,
            emails=emails,
            status="draft",
        )
        saved = self._save_sequence(sequence)
        return saved

    def _build_email_content(self, article: Article) -> List[dict]:
        if self.llm_client is not None:
            prompt = self._build_prompt(article)
            raw = self.llm_client.generate(prompt)
            return self._parse_llm_response(raw, article)

        article_url = f"{self.base_url}/articles/{article.slug or article.id}"
        utm_url = f"{article_url}?utm_source=email&utm_campaign=sequence"
        title = article.title or article.id

        return [
            {
                "subject": f"Привет! Лови бесплатный гайд по теме «{title}»",
                "content": (
                    f"Привет!\n\n"
                    f"Мы подготовили полезный материал про «{title}». "
                    "В нём разобрали все ключевые моменты, которые важно знать.\n\n"
                    f"Читать статью: {utm_url}\n"
                ),
                "delay_days": 0,
            },
            {
                "subject": "Проблема, с которой сталкивается каждый",
                "content": (
                    f"Знакомо ли вам чувство, когда нужно разобраться в теме «{title}»?\n\n"
                    "Мы решили разобрать эту проблему и предложить простое решение.\n\n"
                    f"Полный разбор: {utm_url}\n"
                ),
                "delay_days": 2,
            },
            {
                "subject": "Кейс: как это работает на практике",
                "content": (
                    f"В статье «{title}» мы разобрали реальный пример применения.\n\n"
                    "Не упустите шанс разобраться в теме раз и навсегда.\n\n"
                    f"Читать сейчас: {utm_url}\n"
                ),
                "delay_days": 5,
            },
        ]

    def _build_prompt(self, article: Article) -> str:
        return (
            "Напиши серию из 3 email-писем на русском языке на основе статьи.\n"
            f"Заголовок: {article.title}\n"
            f"Описание: {article.meta_description or article.content[:300]}\n"
            "Структура серии:\n"
            "1. Приветствие + Лид-магнит (полезность)\n"
            "2. Проблема аудитории + решение через продукт\n"
            "3. Кейс/Пример + сильный CTA\n"
            "Для каждого письма:\n"
            "- subject: тема письма\n"
            "- content: тело письма в простом HTML или тексте\n"
            "- delay_days: через сколько дней отправлять (число)\n"
            "Добавляй UTM-метки к ссылкам: utm_source=email&utm_campaign=sequence\n"
            "Ответ в формате JSON: {emails: [{subject, content, delay_days}]}"
        )

    def _parse_llm_response(self, raw: str, article: Article) -> List[dict]:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return self._fallback_emails(article)
        try:
            data = json.loads(match.group())
            emails = data.get("emails", [])
            if not isinstance(emails, list):
                return self._fallback_emails(article)
            return emails[:5]
        except Exception:
            return self._fallback_emails(article)

    def _fallback_emails(self, article: Article) -> List[dict]:
        article_url = f"{self.base_url}/articles/{article.slug or article.id}"
        utm_url = f"{article_url}?utm_source=email&utm_campaign=sequence"
        title = article.title or article.id
        return [
            {
                "subject": f"Привет! Полезный материал про «{title}»",
                "content": f"Привет!\n\nЛови полезный материал про «{title}».\n\nЧитать: {utm_url}\n",
                "delay_days": 0,
            },
            {
                "subject": "Решаем проблему вместе",
                "content": f"Как решить задачу, связанную с «{title}»?\n\nЧитай статью: {utm_url}\n",
                "delay_days": 2,
            },
            {
                "subject": "Кейс + CTA",
                "content": f"Реальный пример по теме «{title}».\n\nНе упускай шанс — читай сейчас: {utm_url}\n",
                "delay_days": 5,
            },
        ]

    def _save_sequence(self, sequence: EmailSequence) -> EmailSequence:
        acquired, msg = self.lock_manager.acquire_lock("email_sequence", sequence.id, "email_sequence_generator")
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            path = write(sequence, "email_sequence")
            sequence.obsidian_path = path
            return sequence
        finally:
            self.lock_manager.release_lock("email_sequence", sequence.id)
