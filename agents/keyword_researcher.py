from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from agents.lock_manager import LockManager
from agents.obsidian_parser import exists, write
from agents.shared_models import Keyword, Offer


class KeywordResearcher:
    def __init__(self, llm_client=None, lock_manager: Optional[LockManager] = None):
        self.llm_client = llm_client
        self.lock_manager = lock_manager or LockManager()

    def research(self, offer: Offer) -> List[Keyword]:
        keywords = self._generate_keywords_via_llm(offer)
        saved_keywords: List[Keyword] = []
        for kw in keywords:
            kw.id = kw.id or f"kw_{uuid.uuid4().hex[:8]}"
            if not self._keyword_exists(kw.text, offer):
                saved = self._save_keyword(kw, offer)
                saved_keywords.append(saved)
        return saved_keywords

    def _generate_keywords_via_llm(self, offer: Offer) -> List[Keyword]:
        if self.llm_client is not None:
            prompt = self._build_prompt(offer)
            raw = self.llm_client.generate(prompt)
            return self._parse_llm_response(raw, offer)
        
        base = offer.name or "оффер"
        bank = offer.bank or ""
        keywords_data = [
            (f"{base} отзыв", "informational", 1000, 30),
            (f"лучший {base}", "commercial", 800, 50),
            (f"оформить {bank} {base}", "transactional", 500, 20),
            (f"{base} как работает", "informational", 1200, 40),
            (f"{bank} {base} сравнить", "commercial", 600, 45),
            (f"{base} онлайн заявка", "transactional", 700, 25),
            (f"{base} условия", "informational", 900, 35),
            (f"что такое {base}", "informational", 1100, 25),
            (f"{base} преимущества", "commercial", 750, 40),
            (f"как получить {base}", "transactional", 650, 30),
        ]
        return [
            Keyword(id=f"kw_{uuid.uuid4().hex[:8]}", text=text, intent=intent, search_volume=volume, difficulty=difficulty)
            for text, intent, volume, difficulty in keywords_data
        ]

    def _build_prompt(self, offer: Offer) -> str:
        return (
            "Сгенерируй 10-15 ключевых слов на русском языке для SEO-статьи о финансовом продукте.\n"
            f"Название: {offer.name}\n"
            f"Банк: {offer.bank or 'Не указан'}\n"
            f"Категория: {offer.category or 'Не указана'}\n"
            f"Целевая аудитория: {offer.target_audience or 'Не указана'}\n"
            "Распредели ключи по интентам: informational, commercial, transactional.\n"
            "Для каждого ключа укажи примерную частотность поиска (High/Medium/Low или число).\n"
            "Верни ответ в формате JSON-списка объектов с полями: text, intent, frequency."
        )

    def _parse_llm_response(self, raw: str, offer: Offer) -> List[Keyword]:
        import json
        import re
        keywords: List[Keyword] = []
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return keywords
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            return keywords
        frequency_map = {"high": 3000, "medium": 1500, "low": 500}
        for item in data:
            text = item.get("text", "")
            intent = item.get("intent", "informational")
            if intent not in {"informational", "commercial", "transactional"}:
                intent = "informational"
            freq = item.get("frequency", "Medium")
            if isinstance(freq, str):
                freq = frequency_map.get(freq.lower(), 1500)
            keywords.append(Keyword(
                id=f"kw_{uuid.uuid4().hex[:8]}",
                text=text,
                intent=intent,
                search_volume=freq,
                difficulty=None,
            ))
        return keywords[:15]

    def _keyword_exists(self, text: str, offer: Offer) -> bool:
        if not exists("keyword", ""):
            return False
        try:
            from agents.obsidian_parser import _OBSIDIAN_ROOT
            kw_dir = _OBSIDIAN_ROOT / "Keywords"
            if not kw_dir.exists():
                return False
            for path in kw_dir.glob("*.md"):
                try:
                    kw = read("keyword", path.stem)
                    if kw.text == text:
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def _save_keyword(self, keyword: Keyword, offer: Offer) -> Keyword:
        lock_id = f"keyword_{keyword.id}"
        acquired, msg = self.lock_manager.acquire_lock("keyword", keyword.id, "keyword_researcher")
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            path = write(keyword, "keyword")
            keyword.obsidian_path = path
            return keyword
        finally:
            self.lock_manager.release_lock("keyword", keyword.id)
