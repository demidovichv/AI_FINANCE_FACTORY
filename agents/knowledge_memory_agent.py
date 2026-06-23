from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from agents.lock_manager import LockManager
from agents.obsidian_parser import exists, read
from agents.shared_models import Article, Keyword


class SimilarityMatch(BaseModel):
    entity_id: str
    entity_type: str
    title: str
    score: float


class KnowledgeMemoryAgent:
    def __init__(self, lock_manager: Optional[LockManager] = None, threshold: float = 0.3):
        self.lock_manager = lock_manager or LockManager()
        self.threshold = threshold

    def check_uniqueness(self, keyword: str, cluster_id: Optional[str] = None) -> dict:
        keyword_tokens = self._tokenize(keyword)
        if not keyword_tokens:
            return {"status": "unique", "message": "OK", "matches": []}

        matches: List[SimilarityMatch] = []
        matches.extend(self._scan_keywords(keyword, keyword_tokens))
        matches.extend(self._scan_articles(keyword, keyword_tokens))
        matches.sort(key=lambda m: m.score, reverse=True)

        if matches:
            best = matches[0]
            if best.score >= self.threshold:
                return {
                    "status": "duplicate",
                    "message": (
                        f"У нас уже есть {best.entity_type} {best.entity_id} "
                        f"по теме «{best.title}» (сходство {best.score:.0%}). "
                        "Рекомендуется написать под другим углом или обновить существующую."
                    ),
                    "matches": [m.model_dump() for m in matches[:5]],
                }
        return {"status": "unique", "message": "OK", "matches": [m.model_dump() for m in matches[:5]]}

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return [w for w in text.split() if len(w) > 2]

    def _scan_keywords(self, keyword: str, keyword_tokens: List[str]) -> List[SimilarityMatch]:
        matches: List[SimilarityMatch] = []
        try:
            from agents.obsidian_parser import _OBSIDIAN_ROOT
            kw_dir = _OBSIDIAN_ROOT / "Keywords"
            if not kw_dir.exists():
                return matches
            for path in kw_dir.glob("*.md"):
                try:
                    kw = read("keyword", path.stem)
                    if kw.text == keyword:
                        matches.append(SimilarityMatch(
                            entity_id=kw.id,
                            entity_type="keyword",
                            title=kw.text,
                            score=1.0,
                        ))
                        continue
                    other_tokens = self._tokenize(kw.text)
                    score = self._similarity(keyword_tokens, other_tokens)
                    if score > 0:
                        matches.append(SimilarityMatch(
                            entity_id=kw.id,
                            entity_type="keyword",
                            title=kw.text,
                            score=score,
                        ))
                except Exception:
                    continue
        except Exception:
            pass
        return matches

    def _scan_articles(self, keyword: str, keyword_tokens: List[str]) -> List[SimilarityMatch]:
        matches: List[SimilarityMatch] = []
        try:
            from agents.obsidian_parser import _OBSIDIAN_ROOT
            articles_dir = _OBSIDIAN_ROOT / "Articles" / "drafts"
            if not articles_dir.exists():
                return matches
            for path in articles_dir.glob("*.md"):
                try:
                    article = read("article", path.stem)
                    title = article.title or article.id
                    if title.lower() == keyword.lower():
                        matches.append(SimilarityMatch(
                            entity_id=article.id,
                            entity_type="article",
                            title=title,
                            score=1.0,
                        ))
                        continue
                    title_tokens = self._tokenize(title)
                    score = self._similarity(keyword_tokens, title_tokens)
                    if score > 0:
                        matches.append(SimilarityMatch(
                            entity_id=article.id,
                            entity_type="article",
                            title=title,
                            score=score,
                        ))
                except Exception:
                    continue
        except Exception:
            pass
        return matches

    def _similarity(self, tokens_a: List[str], tokens_b: List[str]) -> float:
        if not tokens_a or not tokens_b:
            return 0.0
        set_a = set(tokens_a)
        set_b = set(tokens_b)
        intersection = set_a & set_b
        if intersection:
            return 0.8
        for a in set_a:
            for b in set_b:
                if a in b or b in a or a[:3] == b[:3]:
                    return 0.5
        return 0.0
